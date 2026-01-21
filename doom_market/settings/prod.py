from .base import *


if not DEBUG:
    ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

    if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
        if BASE_DOMAIN:
            ALLOWED_HOSTS = [BASE_DOMAIN]
        else:
            raise RuntimeError("ALLOWED_HOSTS must be set in production!")