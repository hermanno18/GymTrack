"""
PWA installability plumbing: manifest.json, service worker, and the
base-template wiring that links/registers them. Kept intentionally
light -- there's no JS test runner in this stack, so these tests only
verify the server-side contract (correct routes/content), not actual
browser install/offline behavior.
"""
import json


def test_manifest_is_served_as_valid_json(client):
    resp = client.get("/static/manifest.json")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["name"] == "GymTrack"
    assert data["display"] == "standalone"
    assert len(data["icons"]) >= 2


def test_service_worker_is_served(client):
    resp = client.get("/static/sw.js")
    assert resp.status_code == 200
    assert b"gymtrack-shell" in resp.data


def test_icons_are_served(client):
    for size in ("192", "512"):
        resp = client.get(f"/static/icons/icon-{size}.png")
        assert resp.status_code == 200


def test_login_page_links_manifest_and_registers_service_worker(client):
    """Checked on a page reachable without auth (login) so this proves
    the wiring lives in base.html for every page, not just logged-in ones."""
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert b'rel="manifest"' in resp.data
    assert b"serviceWorker.register" in resp.data
