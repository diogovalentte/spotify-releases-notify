import base64
import hashlib
import logging
import os
import sys

from cryptography.fernet import Fernet

DEFAULT_DB_FILE_PATH = "/config/config.db"


def get_configs():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    redirect_uri = os.environ.get("REDIRECT_URI")
    ntfy_token = os.environ.get("NTFY_TOKEN")
    ntfy_topic = os.environ.get("NTFY_TOPIC")
    ntfy_url = os.environ.get("NTFY_URL")
    encryption_key = os.environ.get("ENCRYPTION_KEY")
    db_path = os.environ.get("DB_PATH")

    if (
        not client_id
        or not client_secret
        or not redirect_uri
        or not encryption_key
        or not ntfy_token
        or not ntfy_topic
        or not ntfy_url
    ):
        raise Exception("Missing environment variables")

    if not db_path:
        db_path = DEFAULT_DB_FILE_PATH

    if not os.path.isabs(db_path):
        raise Exception("DB_PATH must be an absolute path")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "ntfy_token": ntfy_token,
        "ntfy_topic": ntfy_topic,
        "ntfy_url": ntfy_url,
        "encryption_key": encryption_key,
        "db_path": db_path,
    }


def encrypt_str(s: str):
    configs = get_configs()
    hash = hashlib.md5(configs["encryption_key"].encode()).hexdigest()
    key = base64.urlsafe_b64encode(hash.encode())
    cs = Fernet(key)
    return cs.encrypt(s.encode()).decode()


def decrypt_str(s: str):
    configs = get_configs()
    hash = hashlib.md5(configs["encryption_key"].encode()).hexdigest()
    key = base64.urlsafe_b64encode(hash.encode())
    cs = Fernet(key)
    return cs.decrypt(s.encode()).decode()


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
