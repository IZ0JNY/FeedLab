"""New-version notice: version comparison and 'what's new' taken from the release notes, per language."""
from pathlib import Path

from feedlab import updates

NOTES = (Path(__file__).resolve().parent.parent / "windows" / "RELEASE_NOTES.md").read_text(encoding="utf-8")


def test_version_compare():
    assert updates.is_newer("v0.4.16", "0.4.15")
    assert updates.is_newer("v0.5.0", "0.4.15")
    assert updates.is_newer("v0.4.10", "0.4.9")            # numeric, not alphabetical
    assert not updates.is_newer("v0.4.15", "0.4.15")
    assert not updates.is_newer("v0.4.14", "0.4.15")
    assert not updates.is_newer("", "0.4.15")


def test_notes_per_language():
    it, en = updates.notes_for(NOTES, "it"), updates.notes_for(NOTES, "en")
    assert it and en and it != en
    assert "Novità" not in it and "Requisiti" not in it and "What's new" not in it
    assert it.lstrip().startswith("-") and en.lstrip().startswith("-")


def test_check_shows_notes_only_for_newer(monkeypatch):
    monkeypatch.setattr(updates, "latest_release", lambda timeout=4.0: {"version": "v9.9.9", "url": "u", "body": NOTES})
    info = updates.check("0.4.15", "en")
    assert info["version"] == "9.9.9" and info["notes"] == updates.notes_for(NOTES, "en")
    assert updates.check("9.9.9", "en") is None


def test_offline_or_disabled_is_silent(monkeypatch):
    monkeypatch.setenv("FEEDLAB_NO_UPDATE_CHECK", "1")
    assert updates.latest_release() is None
    assert updates.check("0.0.1") is None


def test_tls_contexts_prefer_the_os_verifier():
    """Windows: the OS certificate check (truststore) comes first; it accepts antivirus/proxy HTTPS scanning."""
    from feedlab import updates
    names = [n for n, _ in updates._contexts()]
    assert names[0] == "truststore" and "certifi" in names
