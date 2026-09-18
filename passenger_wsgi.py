"""
Entry point for cPanel/Passenger (WSGI) hosting on WHC.
Passenger looks for a module-level `application` callable here.
"""
from app import create_app

application = create_app()
