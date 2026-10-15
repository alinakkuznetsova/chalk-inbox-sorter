"""checks the text cleaning works on the kinds of emails that broke the zapier version"""

from sorter import SCHEMA, TAGS, clean, strip_html


def test_html_is_stripped_to_text():
    html = "<html><head><style>p{color:red}</style></head><body><p>Our quiz is <b>cancelled</b> this week</p></body></html>"
    body = clean(strip_html(html))
    assert "cancelled" in body
    assert "<" not in body and "color" not in body


def test_entities_are_decoded():
    assert clean(strip_html("<p>Fish &amp; chips&nbsp;quiz</p>")) == "Fish & chips quiz"


def test_long_bodies_are_truncated():
    assert len(clean("word " * 2000)) <= 2000


def test_schema_only_allows_known_categories():
    assert SCHEMA["schema"]["properties"]["category"]["enum"] == list(TAGS)


def test_every_tag_has_a_hex_colour():
    assert all(colour.startswith("#") and len(colour) == 7 for colour in TAGS.values())
