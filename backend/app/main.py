"""백엔드 진입점.

실행:
    python app/main.py
"""

from app.config import settings
from app.factory import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
