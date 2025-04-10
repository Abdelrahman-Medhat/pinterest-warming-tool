# Pinterest Account Warming Tool

A powerful tool for warming up Pinterest accounts by performing natural interactions with pins. This tool helps maintain account activity and engagement by simulating human-like behavior when interacting with Pinterest content.

## Overview

This tool automates the process of warming up Pinterest accounts by:

1. Logging into Pinterest accounts
2. Browsing the home feed
3. Interacting with pins (opening, liking, saving, commenting)
4. Visiting external links from pins
5. Tracking all interactions and results

The tool is designed to be configurable, allowing you to customize behavior for each account and control the probability of different actions.

## Features

- **Multi-account support**: Process multiple Pinterest accounts simultaneously
- **Configurable behaviors**: Set probability percentages for different actions per account
- **Session management**: Saves and reuses sessions to avoid frequent logins
- **Human-like interactions**: Simulates natural browsing patterns with random delays
- **Detailed logging**: Comprehensive logging of all actions and results
- **Proxy support**: Configure proxies for each account to avoid IP restrictions
- **Rate limiting protection**: Built-in delays and retry mechanisms to avoid Pinterest's rate limits
- **Headless browser option**: Run the browser in headless mode (no GUI) for server environments
- **Configurable link visits**: Enable or disable visiting pin links while maintaining tracking

## Project Structure

```
pinterest_warming-tool/
├── main.py                      # Main entry point for the script
├── config.py                    # Configuration settings
├── accounts.json                # Account credentials and behavior settings
├── comments.json                # Comments to use when commenting on pins
├── pinterest_api/               # Core Pinterest API implementation
│   ├── __init__.py
│   ├── exceptions.py            # Custom exceptions
│   └── mixins/                  # API functionality mixins
│       ├── base.py              # Base API functionality
│       ├── login.py             # Login functionality
│       ├── pin.py               # Pin interaction functionality
│       └── ...
├── pinterest_automation/        # Automation logic
│   ├── __init__.py
│   └── mixins/                  # Automation mixins
│       ├── account_processor_mixin.py  # Account processing logic
│       ├── pin_interaction_mixin.py    # Pin interaction logic
│       └── ...
├── proxy_rotation.py            # Proxy management
└── sessions/                    # Directory for saved sessions
```

## Configuration

### accounts.json

This file contains the account credentials and behavior settings for each account. Each account entry should have the following structure:

```json
[
  {
    "email": "your.email@example.com",
    "password": "your_password",
    "behaviors": {
      "open_pin": 100,
      "like_pin": 80,
      "save_pin": 30,
      "comment_pin": 50,
      "visit_link": 100
    },
    "device_info": {
      "device": "sdk_gphone64_arm64",
      "hardware_id": "66097399e0a69560",
      "manufacturer": "Google",
      "install_id": "68e6437e05c84e57b9cf0833d28dd1c"
    }
  }
]
```

#### Behavior Settings

The `behaviors` object defines the probability (0-100) of performing each action:

- `open_pin`: Probability of opening a pin (default: 100%)
- `like_pin`: Probability of liking a pin (default: 100%)
- `save_pin`: Probability of saving a pin (default: 100%)
- `comment_pin`: Probability of commenting on a pin (default: 100%)
- `visit_link`: Probability of visiting the pin's external link (default: 100%, always enforced)

#### Device Information

The `device_info` object defines the device information used in API requests:

- `device`: Device identifier (used in User-Agent)
- `hardware_id`: Device hardware ID
- `manufacturer`: Device manufacturer
- `install_id`: Installation ID

### comments.json

This file contains a list of comments to use when commenting on pins:

```json
[
  "Great pin! Thanks for sharing.",
  "Love this! Saving for later.",
  "Amazing content!",
  "This is exactly what I was looking for.",
  "Thanks for sharing this useful information."
]
```

### config.py

This file contains global configuration settings:

```python
# Number of pins to process per account
NUM_PINS_TO_PROCESS = 10

# Maximum number of parallel workers
MAX_WORKERS = 1

# Browser settings
HEADLESS_BROWSER = False  # Set to True to run browser in headless mode (no GUI)
ENABLE_PIN_LINK_VISITS = True  # Set to False to disable visiting pin links (tracking requests will still be sent)

# Path to accounts file
ACCOUNTS_FILE = "accounts.json"

# Path to comments file
COMMENTS_FILE = "comments.json"
```

#### Browser Settings

The `HEADLESS_BROWSER` setting controls whether the browser runs in headless mode (no GUI):

- `True`: Browser runs in headless mode, which is useful for server environments or when you don't need to see the browser window
- `False`: Browser runs in visible mode, which is useful for debugging or when you want to see the browser interactions

#### Link Visit Settings

The `ENABLE_PIN_LINK_VISITS` setting controls whether the tool will actually visit pin links in a browser:

- `True`: Tool will visit pin links in a browser (default)
- `False`: Tool will skip visiting pin links but still send tracking requests to Pinterest

This is useful when you want to:
- Reduce resource usage by not opening browser windows
- Avoid potential issues with external websites
- Still maintain tracking data for Pinterest analytics
- Run in environments where browser automation is not possible

## Usage

### Basic Usage

1. Configure your accounts in `accounts.json`
2. Configure your comments in `comments.json` (optional)
3. Run the script:

```bash
python main.py
```

### Advanced Configuration

#### Proxy Configuration

To use proxies, add proxy information to your accounts in `accounts.json`:

```json
{
  "email": "your.email@example.com",
  "password": "your_password",
  "behaviors": { ... },
  "device_info": { ... },
  "proxy": {
    "http": "http://username:password@proxy.example.com:8080",
    "https": "http://username:password@proxy.example.com:8080"
  }
}
```

#### Customizing Behavior

You can customize the behavior of each account by adjusting the probability values in the `behaviors` object. For example, to make an account only like pins 50% of the time and never comment:

```json
"behaviors": {
  "open_pin": 100,
  "like_pin": 50,
  "save_pin": 0,
  "comment_pin": 0,
  "visit_link": 100
}
```

#### Device Information

You can customize the device information for each account to simulate different devices:

```json
"device_info": {
  "device": "SM-G973F",
  "hardware_id": "a1b2c3d4e5f6g7h8",
  "manufacturer": "Samsung",
  "install_id": "f1e2d3c4b5a69788"
}
```

#### Headless Browser Mode

To run the browser in headless mode (no GUI), set the `HEADLESS_BROWSER` option to `True` in `config.py`:

```python
# Browser settings
HEADLESS_BROWSER = True  # Run browser in headless mode (no GUI)
```

This is useful for server environments or when you don't need to see the browser window. It can also reduce resource usage and improve performance.

#### Disabling Link Visits

To disable visiting pin links while still maintaining tracking data, set the `ENABLE_PIN_LINK_VISITS` option to `False` in `config.py`:

```python
# Browser settings
ENABLE_PIN_LINK_VISITS = False  # Disable visiting pin links (tracking requests will still be sent)
```

This is useful when you want to:
- Reduce resource usage by not opening browser windows
- Avoid potential issues with external websites
- Still maintain tracking data for Pinterest analytics
- Run in environments where browser automation is not possible

## Troubleshooting

### Common Issues

1. **Login Failures**: If you're experiencing login failures, check your credentials and ensure your account is not locked.

2. **Rate Limiting**: If you're hitting rate limits, try:
   - Reducing the number of pins processed
   - Increasing delays between actions
   - Using different proxies for each account

3. **Session Errors**: If you're experiencing session errors, try deleting the session files in the `sessions` directory and running the script again.

4. **Headless Browser Issues**: If you're experiencing issues with headless mode, try:
   - Setting `HEADLESS_BROWSER = False` in `config.py` to run in visible mode
   - Ensuring your server has the necessary dependencies for headless Chrome
   - Adding additional Chrome options if needed (e.g., `--no-sandbox`, `--disable-dev-shm-usage`)

5. **Link Visit Issues**: If you're experiencing issues with visiting pin links, try:
   - Setting `ENABLE_PIN_LINK_VISITS = False` in `config.py` to disable link visits
   - Checking if the external websites are accessible from your network
   - Verifying that your browser automation setup is working correctly

### Logs

The script provides detailed logs of all actions and results. Check the console output for information about what's happening and any errors that occur.

## Security Considerations

- **Credentials**: Never share your `accounts.json` file as it contains sensitive information.
- **Sessions**: The `sessions` directory contains authentication tokens. Keep this directory secure.
- **Proxies**: If using proxies, ensure they are secure and not logging your traffic.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use it responsibly and in accordance with Pinterest's terms of service. The developers are not responsible for any misuse of this tool or any consequences that may arise from its use. 