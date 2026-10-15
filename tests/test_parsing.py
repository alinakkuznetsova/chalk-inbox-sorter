"""checks the email parsing works on the kinds of emails that broke the zapier version"""

from email.message import EmailMessage

from sorter import FOLDERS, SCHEMA, get_body, parse_email


def make_email(plain=None, html=None, subject="Quiz night on Thursday"):
    msg = EmailMessage()
    msg["From"] = "The Red Lion <events@redlion.co.uk>"
    msg["To"] = "hello@findchalk.com"
    msg["Subject"] = subject
    msg["Date"] = "Wed, 14 Oct 2026 18:30:00 +0100"
    msg["Message-ID"] = "<abc123@redlion.co.uk>"
    if plain is not None:
        msg.set_content(plain)
    if html is not None:
        if plain is None:
            msg.set_content(html, subtype="html")
        else:
            msg.add_alternative(html, subtype="html")
    return msg


def test_plain_text_email():
    parsed = parse_email(bytes(make_email(plain="Hi, can we list our Thursday quiz?")))
    assert parsed["body"] == "Hi, can we list our Thursday quiz?"
    assert parsed["from_email"] == "events@redlion.co.uk"
    assert parsed["message_id"] == "<abc123@redlion.co.uk>"
    assert parsed["received_at"].startswith("2026-10-14T18:30")


def test_html_only_email_is_stripped_to_text():
    html = "<html><head><style>p{color:red}</style></head><body><p>Our quiz is <b>cancelled</b> this week</p></body></html>"
    body = get_body(make_email(html=html))
    assert "cancelled" in body
    assert "<" not in body and "color" not in body


def test_plain_text_is_preferred_over_html():
    body = get_body(make_email(plain="plain version", html="<p>html version</p>"))
    assert body == "plain version"


def test_long_bodies_are_truncated():
    body = get_body(make_email(plain="word " * 2000))
    assert len(body) <= 2000


def test_encoded_subject_is_decoded():
    parsed = parse_email(bytes(make_email(plain="hi", subject="Café quiz 🍺")))
    assert parsed["subject"] == "Café quiz 🍺"


def test_schema_only_allows_known_categories():
    allowed = SCHEMA["schema"]["properties"]["category"]["enum"]
    assert allowed == list(FOLDERS)
    assert all("&" not in folder for folder in FOLDERS.values())
