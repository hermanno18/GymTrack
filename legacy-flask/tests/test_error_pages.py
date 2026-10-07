"""
Custom themed 404/500 error pages (see app/__init__.py's
_register_error_handlers). Kept out of test_pwa.py/etc since this is a
distinct concern -- error UX, not installability.
"""


def test_unknown_url_shows_custom_404_page(client):
    resp = client.get("/this-route-does-not-exist")
    assert resp.status_code == 404
    assert b"Page not found" in resp.data
    assert b"Back to GymTrack" in resp.data


def test_unhandled_exception_shows_custom_500_page_and_rolls_back_session(app):
    """Flask only invokes registered error handlers for *unhandled*
    exceptions when PROPAGATE_EXCEPTIONS is False -- by default it's
    None, which resolves to True whenever TESTING/DEBUG is on (as our
    test app fixture has it), so Flask would normally re-raise instead
    of rendering our 500 page. Overriding it here is the standard way
    to actually exercise a 500 handler under the test client instead of
    just trusting it looks right by inspection.

    A throwaway route is registered directly on the app instance for
    this one test only -- it never pollutes the real blueprint routes.
    """
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.route("/__test_explode")
    def _explode():
        raise RuntimeError("intentional explosion for test coverage")

    client = app.test_client()
    resp = client.get("/__test_explode")
    assert resp.status_code == 500
    assert b"Something went wrong" in resp.data
    assert b"Back to GymTrack" in resp.data
