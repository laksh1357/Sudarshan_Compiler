"""
Vercel Serverless Function entry point for Sudarshan Compiler Studio.
"""

import sys
import os

# Compute root and source paths portably in Vercel Lambda environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.main import app

# Expose app for Vercel ASGI serverless handler
handler = app
