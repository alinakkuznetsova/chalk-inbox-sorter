"""checks the move logic against a fake mail server"""

import imaplib

from sorter import move


class FakeImap:
    def __init__(self, supports_move):
        self.supports_move = supports_move
        self.calls = []

    def uid(self, command, *args):
        self.calls.append((command, *args))
        if command == "MOVE" and not self.supports_move:
            raise imaplib.IMAP4.error("BAD unknown command")
        return "OK", [b""]

    def expunge(self):
        self.calls.append(("EXPUNGE",))
        return "OK", [b""]


def test_uses_move_when_supported():
    imap = FakeImap(supports_move=True)
    move(imap, b"42", "Venue Enquiries")
    assert imap.calls == [("MOVE", b"42", '"Venue Enquiries"')]


def test_falls_back_to_copy_and_delete():
    imap = FakeImap(supports_move=False)
    move(imap, b"42", "Venue Enquiries")
    commands = [c[0] for c in imap.calls]
    assert commands == ["MOVE", "COPY", "STORE", "EXPUNGE"]
