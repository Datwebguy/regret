from pathlib import Path

from regret.api.main import _public_file

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "Authorize REGRET",
    "By allowing REGRET to access your Alpaca account",
    "access to your account information",
    "authorization to place transactions at your direction",
    "Alpaca does not warrant or guarantee",
    "learn more about REGRET",
)


def test_disclosure_copy_matches_alpaca_required_language():
    source = (ROOT / "web" / "src" / "lib" / "alpacaDisclosure.ts").read_text(encoding="utf-8")
    settings = (ROOT / "web" / "src" / "pages" / "Settings.tsx").read_text(encoding="utf-8")
    for phrase in REQUIRED:
        assert phrase in source
    assert "ALPACA_DISCLOSURE_TITLE" in settings
    assert ">Deny<" in settings
    assert ">Allow<" in settings


def test_legal_pages_still_public():
    assert _public_file("terms.html") is not None
    assert _public_file("privacy.html") is not None
