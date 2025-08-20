from .settings import *  # noqa

# Use SQLite for tests to avoid external DB dependencies
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable email backend networking in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Faster hasher and no migrations optimizations can be added later if needed.
