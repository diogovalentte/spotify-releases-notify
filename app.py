from src.api import app
from src.db import (
    create_db,
)


def main():
    create_db()
    app.run()


if __name__ == "__main__":
    main()
