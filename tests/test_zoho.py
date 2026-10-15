"""checks the zoho calls against a fake http client, so no real inbox is touched"""

import pytest

from sorter import TAGS, ZohoMail, as_id


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeHttp:
    def __init__(self, labels=()):
        self.calls = []
        self.labels = list(labels)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return Response({"access_token": "token123"})

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url.endswith("/api/accounts"):
            return Response({"data": [{"accountId": "999"}]})
        if url.endswith("/labels") and method == "GET":
            return Response({"data": self.labels})
        if url.endswith("/labels") and method == "POST":
            return Response({"data": {"labelId": f"id-{kwargs['json']['displayName']}"}})
        if url.endswith("/folders"):
            return Response({"data": [{"folderName": "Sent", "folderId": "1"}, {"folderName": "Inbox", "folderType": "Inbox", "folderId": "2"}]})
        return Response({"data": {}})


def make(http):
    return ZohoMail("cid", "secret", "refresh", region="uk", http=http)


def test_uses_uk_servers_and_refresh_token():
    http = FakeHttp()
    zoho = make(http)
    method, url, kwargs = http.calls[0]
    assert url == "https://accounts.zoho.uk/oauth/v2/token"
    assert kwargs["params"]["grant_type"] == "refresh_token"
    assert zoho.account_id == "999"
    assert http.calls[1][1] == "https://mail.zoho.uk/api/accounts"
    assert http.calls[1][2]["headers"]["Authorization"] == "Zoho-oauthtoken token123"


def test_finds_inbox():
    assert make(FakeHttp()).inbox_id() == "2"


def test_creates_only_missing_tags_with_colours():
    http = FakeHttp(labels=[{"displayName": "Other", "labelId": "77"}])
    tags = make(http).ensure_tags()
    created = [c[2]["json"] for c in http.calls if c[0] == "POST" and c[1].endswith("/labels")]
    assert {c["displayName"] for c in created} == set(TAGS) - {"Other"}
    assert all(c["color"] == TAGS[c["displayName"]] for c in created)
    assert tags["Other"] == "77"
    assert tags["Venue Enquiries"] == "id-Venue Enquiries"


def test_apply_tag_and_flag_payloads():
    http = FakeHttp()
    zoho = make(http)
    zoho.apply_tag("123456", "55")
    zoho.flag("123456")
    tag_call, flag_call = http.calls[-2:]
    assert tag_call[0] == "PUT" and tag_call[1].endswith("/accounts/999/updatemessage")
    assert tag_call[2]["json"] == {"mode": "applyLabel", "messageId": [123456], "labelId": ["55"]}
    assert flag_call[2]["json"] == {"mode": "setFlag", "messageId": [123456], "flagid": "important"}


def test_token_failure_is_loud():
    class BadHttp(FakeHttp):
        def post(self, url, **kwargs):
            return Response({"error": "invalid_code"})

    with pytest.raises(RuntimeError):
        make(BadHttp())


def test_as_id():
    assert as_id("42") == 42
    assert as_id("abc") == "abc"
