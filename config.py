"""
Configuration settings for Pinterest automation.
"""

# Number of pins to process per account
NUM_PINS_TO_PROCESS = 1

# Maximum number of concurrent workers
MAX_WORKERS = 5

# Browser settings
HEADLESS_BROWSER = False  # Set to True to run browser in headless mode (no GUI)

# File paths
ACCOUNTS_FILE = "accounts.json"
COMMENTS_FILE = "comments.json" 