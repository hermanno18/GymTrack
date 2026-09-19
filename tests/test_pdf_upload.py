"""
PDF upload tests. The real pdfplumber extraction is monkeypatched so these
tests focus on GymTrack's own logic: file-type validation, and the two
fallback paths (unreadable file / unparseable text) versus the happy path.
"""
import io

from app.models import Program
import app.programs as programs_module


def _register(client, email="pdfuser@example.com"):
    return client.post("/auth/register", data={
        "email": email, "password": "testpass123", "confirm": "testpass123",
    }, follow_redirects=True)


def test_rejects_non_pdf_extension(client):
    _register(client)
    data = {"pdf": (io.BytesIO(b"not a pdf"), "program.txt")}
    resp = client.post(
        "/programs/new/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"Only PDF files" in resp.data


def test_missing_file_shows_error(client):
    _register(client)
    resp = client.post("/programs/new/upload", data={}, follow_redirects=True)
    assert b"choose a PDF" in resp.data


def test_unreadable_pdf_does_not_create_a_program(client, app, monkeypatch):
    _register(client)
    monkeypatch.setattr(
        programs_module, "_extract_pdf_text",
        lambda uploaded_file: (None, "That file couldn't be read as a PDF."),
    )
    data = {"pdf": (io.BytesIO(b"%PDF-garbage"), "program.pdf")}
    resp = client.post(
        "/programs/new/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"couldn" in resp.data.lower()
    with app.app_context():
        assert Program.query.count() == 0


def test_unparseable_text_falls_back_to_blank_manual_builder(client, app, monkeypatch):
    _register(client)
    monkeypatch.setattr(
        programs_module, "_extract_pdf_text",
        lambda uploaded_file: ("just some random unstructured notes", None),
    )
    data = {"pdf": (io.BytesIO(b"%PDF-1.4 fake"), "program.pdf")}
    resp = client.post(
        "/programs/new/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"manually" in resp.data.lower()
    with app.app_context():
        program = Program.query.first()
        assert program is not None
        assert program.days == []


def test_parseable_text_creates_days_and_exercises(client, app, monkeypatch):
    _register(client)
    sample_text = "Day1: Squat 4x8 @60kg; Bench Press 3x10"
    monkeypatch.setattr(
        programs_module, "_extract_pdf_text",
        lambda uploaded_file: (sample_text, None),
    )
    data = {"pdf": (io.BytesIO(b"%PDF-1.4 fake"), "program.pdf")}
    resp = client.post(
        "/programs/new/upload", data=data,
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert b"imported" in resp.data.lower()
    with app.app_context():
        program = Program.query.first()
        assert len(program.days) == 1
        assert program.days[0].label == "Day1"
        assert len(program.days[0].exercises) == 2
