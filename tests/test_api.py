"""The page's calls, and the promise behind the zeros on it."""

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import ingest
from app.api import app
from app.sources import ROOT

APP_DIR = ROOT / "app"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "store.db"))
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    return TestClient(app)


def test_the_page_and_its_files_are_served_with_nothing_from_outside(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "<title>Silent context capture</title>" in page.text
    for path in ("/web/app.js", "/web/style.css"):
        assert client.get(path).status_code == 200
    for name in ("index.html", "app.js", "style.css"):
        text = (ROOT / "web" / name).read_text(encoding="utf-8")
        assert "http://" not in text.replace("http://www.w3.org/2000/svg", "")
        assert "https://" not in text


def test_moving_the_clock_needs_no_model_and_decides_what_is_known(client: TestClient) -> None:
    before = client.post("/clock", json={"as_of": "2026-10-14T22:00:00"}).json()
    assert before["as_of"] == "2026-10-14T22:00:00"
    assert len(before["claims"]) == 1
    known = {source["file"]: source["known"] for source in before["sources"]}
    assert known["email_key_nilo.txt"] is True
    assert known["teams_trn042.json"] is False

    after = client.post("/clock", json={"as_of": "2026-10-15T00:00:00"}).json()
    assert len(after["claims"]) == 2
    assert all(s["mode"] == "recorded" for s in after["sources"] if s["known"])


def test_the_state_shows_elisas_files_as_unchanged(client: TestClient) -> None:
    state = client.post("/clock", json={"as_of": "2026-10-15T00:00:00"}).json()
    elisa = [source for source in state["sources"] if source["origin"] == "elisa"]
    assert len(elisa) == 2
    assert all(source["unchanged"] is True for source in elisa)


def test_events_show_also_the_future_marked_as_unknown(client: TestClient) -> None:
    state = client.post("/clock", json={"as_of": "2026-10-15T00:00:00"}).json()
    firmware = next(e for e in state["events"] if e["type"] == "firmware_updated")
    assert firmware["known"] is False
    replaced = next(e for e in state["events"] if e["id"] == "ev-101")
    assert replaced["known"] is True


def test_the_metrics_hold_the_zeros_and_the_held_out_runs(client: TestClient) -> None:
    metrics = client.post("/clock", json={"as_of": "2026-11-03T00:00:00"}).json()["metrics"]
    assert metrics["conversations_started"] == 0
    assert metrics["actions_asked_of_specialists"] == 0
    assert metrics["waiting"] == 1
    assert metrics["held_out_wrong_per_run"] == [0, 0, 0, 1, 1]


def test_a_gap_shows_in_the_state_by_group(client: TestClient) -> None:
    client.post("/clock", json={"as_of": "2026-10-14T22:00:00"})
    client.post("/claims_for", json={"entity": "TRN-051", "symptom": "anything at all"})
    groups = client.get("/state").json()["metrics"]["gaps_by_group"]
    assert groups == {"transmission-oncall": 1}


def test_a_fresh_start_clears_the_logs_and_a_plain_move_keeps_them(client: TestClient) -> None:
    clock = "2026-10-14T22:00:00"
    client.post("/clock", json={"as_of": clock})
    client.post("/claims_for", json={"entity": "TRN-051", "symptom": "anything at all"})
    kept = client.post("/clock", json={"as_of": clock}).json()
    assert kept["metrics"]["gaps_by_group"] == {"transmission-oncall": 1}
    cleared = client.post("/clock", json={"as_of": clock, "fresh": True}).json()
    assert cleared["metrics"]["gaps_by_group"] == {}


def test_a_source_opens_as_it_was_read(client: TestClient) -> None:
    source = client.get("/source", params={"file": "teams_trn042.json"}).json()
    assert source["origin"] == "elisa"
    assert source["original_name"] == "teams_chat.json"
    assert source["messages"][0]["seq"] == 1
    assert len(source["sha256"]) == 64


@pytest.mark.parametrize(
    "file", ["../../.env", "../truth/expected_decoys.json", "manifest.json", "/etc/passwd"]
)
def test_only_files_in_the_manifest_can_be_opened(client: TestClient, file: str) -> None:
    assert client.get("/source", params={"file": file}).status_code == 404


def test_without_a_record_or_a_model_the_clock_says_what_is_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(*args: object, **kwargs: object) -> None:
        raise ingest.llm.ModelNotConfigured("LLM_API_KEY and LLM_MODEL are not set")

    monkeypatch.setattr(ingest, "ingest_file", missing)
    response = client.post("/clock", json={"as_of": "2026-10-15T00:00:00"})
    assert response.status_code == 409
    assert "LLM_API_KEY" in response.json()["detail"]


def test_nothing_in_the_product_can_post_to_a_channel() -> None:
    """The zero on the page is by construction: only the model client reaches outside."""
    outward = {
        "smtplib", "requests", "httpx", "httpx2", "urllib", "aiohttp", "socket", "http", "ftplib",
        "telnetlib", "subprocess",
    }
    reach = {}
    for path in APP_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if root in outward or root == "openai":
                    reach.setdefault(path.name, set()).add(root)
    assert reach == {"llm.py": {"openai"}}
