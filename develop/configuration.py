"""
Netbox configuration for local development environment
"""

import os
import sys

DEBUG = True
DEVELOPER = True
TEST_MODE = len(sys.argv) > 1 and sys.argv[1] == "test"

ALLOWED_HOSTS = ["*"]
CORS_ORIGIN_ALLOW_ALL = True
CHANGELOG_RETENTION = 7
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]
PLUGINS = ["netbox_device_view", "netbox_custom_objects"]


TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "12345678901234567890123456789012345678901234567890"
)

DATABASE = {
    "HOST": "postgres",
    "PORT": "",
    "NAME": "netbox",
    "USER": os.environ.get("POSTGRES_USER", "netbox"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
    "CONN_MAX_AGE": 0,
}

REDIS = {
    "tasks": {
        "DATABASE": 0,
        "HOST": os.environ.get("REDIS_HOST", "redis"),
        "PORT": 6379,
        "PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
        "SSL": False,
    },
    "caching": {
        "DATABASE": 1,
        "HOST": os.environ.get("REDIS_HOST", "redis"),
        "PORT": 6379,
        "PASSWORD": os.environ.get("REDIS_PASSWORD", ""),
        "SSL": False,
    },
}
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'normal': {
            'format': '%(asctime)s %(name)s %(levelname)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        # This handler logs to the console (stdout)
        'console': {
            'level': 'DEBUG',  # Set the handler to accept all levels
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'normal',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO', # Keep Django at INFO
        },
        'netbox': {
            'handlers': ['console'],
            'level': 'INFO', # Keep the main netbox logger at INFO
        },

        # --- THIS IS THE MAGIC PART ---
        # This will show script loading errors in your Docker logs
        'netbox.data_backends': {
            'handlers': ['console'],
            'level': 'DEBUG', 
        },
        # ------------------------------

        'rq.worker': {
            'handlers': ['console'],
            'level': 'INFO', # Keep RQ worker at INFO
        },
    },
}