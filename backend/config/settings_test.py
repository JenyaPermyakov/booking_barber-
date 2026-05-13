import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("BOT_TOKEN", "test-bot-token")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")
os.environ.setdefault("DB_NAME", ":memory:")
os.environ.setdefault("DB_USER", "")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("DB_HOST", "")
os.environ.setdefault("DB_PORT", "")

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DEBUG = False
