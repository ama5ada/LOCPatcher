"""
All hard-coded values that I may change but users should not configure
"""

REMOTE_PATCH_LIST = "https://loc.iambvc.it/client/patchlist.txt"
REMOTE_HOST = "https://loc.iambvc.it/client/"
REQUEST_TIMEOUT = 30
MAX_RETRIES  = 3
RETRY_BASE_DELAY  = 2.0
USER_AGENT        = "LOCPatcher/2.0"
# 128 KB read buffer
DOWNLOAD_CHUNK = 131_072

# Application
APP_TITLE = "Last Oasis Classic Launcher"
APP_NAME = "LOCPatcher"
APP_AUTHOR = "LastOasisClassic"
LOG_DIR = "patcher_logs"
# 5 MB
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3