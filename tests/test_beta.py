"""BETA TEST builds (when EXPIRY is on): 30 days from the first start of each version, clock rollback counts as expired."""
import pytest

from feedlab import beta


@pytest.fixture(autouse=True)
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("FEEDLAB_CONFIG", str(tmp_path))
    monkeypatch.setattr(beta, "BETA", True)
    monkeypatch.setattr(beta, "EXPIRY", True)
    return tmp_path


def test_thirty_days(monkeypatch):
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-01T10:00:00")
    s = beta.status("9.9.9")
    assert not s["expired"] and s["days_left"] == 30
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-30T09:00:00")
    assert not beta.status("9.9.9")["expired"]
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-31T10:00:01")
    s = beta.status("9.9.9")
    assert s["expired"] and s["reason"] == "scaduta" and s["days_left"] == 0


def test_new_version_gets_its_own_days(monkeypatch):
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-01T10:00:00")
    beta.status("1.0.0")
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2027-02-01T10:00:00")
    assert beta.status("1.0.0")["expired"]
    assert not beta.status("1.0.1")["expired"]


def test_clock_moved_back(monkeypatch):
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-10T10:00:00")
    beta.status("2.0.0")
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2026-12-05T10:00:00")
    s = beta.status("2.0.0")
    assert s["expired"] and s["reason"] == "orologio"


def test_release_build(monkeypatch):
    monkeypatch.setattr(beta, "BETA", False)
    assert beta.status()["expired"] is False


def test_no_expiry_by_default(monkeypatch):
    monkeypatch.setattr(beta, "EXPIRY", False)
    monkeypatch.setenv("FEEDLAB_BETA_NOW", "2030-01-01T10:00:00")
    s = beta.status("0.4.15")
    assert s["beta"] and not s["expiry"] and not s["expired"] and s["days_left"] is None


def test_shipped_without_expiry():
    import importlib
    assert importlib.reload(beta).EXPIRY is False
