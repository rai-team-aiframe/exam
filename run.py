# run.py
import os
import sys

# Add the parent directory to Python path to allow proper imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5000, reload=True)