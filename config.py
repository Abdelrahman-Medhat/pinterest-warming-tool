"""
Configuration settings for Pinterest automation.
"""

# Number of pins to process per account
NUM_PINS_TO_PROCESS = 1

# Maximum number of parallel workers
MAX_WORKERS = 1

# Browser settings
HEADLESS_BROWSER = False  # Set to True to run browser in headless mode (no GUI)
ENABLE_PIN_LINK_VISITS = False  # Set to False to disable visiting pin links (tracking requests will still be sent)

# Path to accounts file
ACCOUNTS_FILE = "accounts.json"

# Path to comments file
COMMENTS_FILE = "comments.json"

# Specific pins to process and their actions
# If not empty, the tool will process these pins instead of fetching from feeds
# Format: List of dictionaries with pin_id and actions to perform
# Each action (like, save, comment, visit) is either True or False
SPECIFIC_PINS = [
    # Example - Uncomment and edit with real pin IDs to use this feature:
    # {
    #     "pin_id": "425871708532790116",
    #     "actions": {
    #         "like": True,
    #         "save": True,
    #         "comment": True,
    #         "visit": True
    #     }
    # }
] 