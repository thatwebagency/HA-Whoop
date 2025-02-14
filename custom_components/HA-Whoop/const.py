"""Constants for the Whoop integration."""
from datetime import timedelta

DOMAIN = "whoop"
SCAN_INTERVAL = 300  # 5 minutes

# Configuration
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
OAUTH_AUTHORIZE_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
OAUTH_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
# API
API_BASE_URL = "https://api.prod.whoop.com/developer/v1/"
API_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_AUTHORIZE_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
AUTH_CALLBACK_PATH = "/api/whoop/callback"
AUTH_CALLBACK_NAME = "api:whoop:callback"
# Endpoints
ENDPOINT_RECOVERY = "/recovery"
ENDPOINT_SLEEP = "/sleep"
ENDPOINT_CYCLE = "/cycle"
ENDPOINT_USER = "/user"

# Sensor types
SENSOR_TYPES = {
    "recovery_score": {
        "name": "Recovery Score",
        "unit": "%",
        "icon": "mdi:heart-pulse",
    },
    "resting_heart_rate": {
        "name": "Resting Heart Rate",
        "unit": "bpm",
        "icon": "mdi:heart",
    },
    "sleep_score": {
        "name": "Sleep Score",
        "unit": "%",
        "icon": "mdi:sleep",
    },
    "sleep_duration": {
        "name": "Sleep Duration",
        "unit": "hours",
        "icon": "mdi:clock",
    },
    "strain_score": {
        "name": "Strain Score",
        "unit": None,
        "icon": "mdi:lightning-bolt",
    },
}

# Error messages
ERROR_AUTH = "Authentication failed"
ERROR_CONNECTION = "Connection failed"
ERROR_UNKNOWN = "Unknown error occurred"

DEFAULT_TIMEOUT = 10
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=5)