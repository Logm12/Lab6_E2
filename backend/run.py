import os
import sys
import traceback

def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv()


if __name__ == "__main__":
    try:
        _load_dotenv_if_available()
        from app.main import app

        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8000"))
        import uvicorn

        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
