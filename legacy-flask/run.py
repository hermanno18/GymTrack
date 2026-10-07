"""
Local development entry point. Not used in production (WHC uses
passenger_wsgi.py via cPanel's Passenger). Run with:

    python run.py
"""
import os
import webbrowser
import threading

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    url = f"http://127.0.0.1:{port}"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=True)
