# Selenium Teleport

Save and restore browser cookies, `localStorage`, and `sessionStorage` for Selenium sessions.

[![CI](https://github.com/godhiraj-code/selenium-teleport/actions/workflows/ci.yml/badge.svg)](https://github.com/godhiraj-code/selenium-teleport/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-2.1.1-green.svg)](https://pypi.org/project/selenium-teleport/)

Selenium Teleport captures state from the browser's current origin, writes it to a file, then restores it after navigating a new browser to the destination origin. This can avoid repeated logins when the target site's authentication model accepts restored browser state.

## What it saves

- Cookies visible to Selenium on the current page
- `localStorage` for the current origin
- `sessionStorage` for the current origin
- IndexedDB database names, versions, and object-store names as diagnostic metadata

IndexedDB records are **not** exported or restored. The library does not capture state from every origin visited by the browser. Some applications also bind sessions to devices, IP addresses, server-side state, or other signals, so a restored file does not guarantee an authenticated session.

## Installation

```bash
# Regular Selenium support
pip install selenium-teleport

# Optional undetected-chromedriver integration
pip install selenium-teleport[undetected]

# Optional sb-stealth-wrapper integration
pip install selenium-teleport[stealth]

# Optional Fernet encryption
pip install selenium-teleport[security]

# All optional integrations
pip install selenium-teleport[undetected,stealth,security]
```

The base installation uses Selenium's regular Chrome driver by default. Browser and driver availability are still managed by Selenium and the local environment.

## Quick start

```python
from selenium_teleport import Teleport, create_driver

# Regular Selenium is the default; set use_undetected=True only after
# installing selenium-teleport[undetected].
driver = create_driver(profile_path="my_profile")

try:
    with Teleport(driver, "session.json") as teleport:
        if teleport.has_state():
            teleport.load("https://example.com/dashboard")
        else:
            driver.get("https://example.com/login")
            # Complete login here. State is saved on successful context exit.
finally:
    driver.quit()
```

`Teleport` auto-saves only when the context exits without an exception. Auto-save errors are logged; call `teleport.save()` directly if the caller must handle save failures.

## Encryption

State files contain authentication material. Prefer encryption and keep the key outside source control.

```python
import os

from selenium_teleport import Teleport, create_driver

# TELEPORT_ENCRYPTION_KEY must contain an existing Fernet key.
# Generate one separately with selenium_teleport.generate_key().
os.environ["TELEPORT_ENCRYPTION_KEY"] = "your-fernet-key"

driver = create_driver()
try:
    with Teleport(driver, "session.enc", encrypt=True) as teleport:
        if teleport.has_state():
            teleport.load("https://example.com/dashboard")
        else:
            driver.get("https://example.com/login")
finally:
    driver.quit()
```

Setting `TELEPORT_ENCRYPTION_KEY` supplies a key but does not by itself encrypt saves. Pass `encrypt=True` to `Teleport`, `teleport_session`, `save_state`, or `save_state_stealth`.

## Restore behavior and safety checks

`load_state(driver, file_path, destination_url)` performs these steps:

1. Rejects non-HTTP(S) destination URLs and literal loopback, link-local, private, reserved, or otherwise non-public IP addresses.
2. Applies `TELEPORT_ALLOWED_DOMAINS` and `TELEPORT_BLOCKED_DOMAINS` when configured.
3. Validates the saved source against the destination.
   - State containing `localStorage` or `sessionStorage` must be restored to the same origin (scheme, host, and effective port).
   - Cookie-only state may be restored across subdomains that resolve to the same supported root-domain form.
4. Removes expired cookies by default and raises `ExpiredSessionError` if every saved cookie has expired.
5. Navigates to the destination origin, injects cookies and origin storage, then navigates to the full destination URL.

URL validation does not resolve hostnames before navigation, so it does not protect against a public hostname that resolves to a private address or changes resolution between checks. Treat destination URLs as trusted application input even when validation is enabled.

Path sanitization rejects parent-directory traversal syntax. It is not a filesystem sandbox unless the calling application also controls the directory in which state files may be written.

## API reference

### State management

| Function | Description |
|---|---|
| `save_state(driver, file_path, encrypt=False, encryption_key=None)` | Save current-origin cookies and storage |
| `load_state(driver, file_path, destination_url, validate_expiry=True, validate_domain=True)` | Validate and restore state, then navigate |
| `delete_state(file_path, secure=True)` | Best-effort overwrite, then delete the state file |
| `get_state_info(file_path, encryption_key=None)` | Return state-file metadata and item counts |

`delete_state(..., secure=True)` performs a best-effort overwrite. Filesystems, snapshots, journaling, and storage hardware can retain copies; this is not a guarantee of forensic erasure or regulatory compliance.

### Context managers

| API | Description |
|---|---|
| `Teleport(driver, file_path, auto_save=True, encrypt=False)` | Object-oriented load/save context manager |
| `teleport_session(driver, file_path, destination_url=None, encrypt=False)` | Functional context manager |

### Optional stealth integration

```python
from selenium_teleport import load_state_stealth, save_state_stealth
from sb_stealth_wrapper import StealthBot

with StealthBot(success_criteria="Dashboard") as bot:
    load_state_stealth(bot, "state.json", "https://example.com/dashboard")
    # Continue automation.
    save_state_stealth(bot, "state.json")
```

These helpers use `bot.sb` for state access. They do not guarantee bot-detection or challenge bypass; results depend on the site, browser, dependency versions, and environment.

### Driver creation

| Parameter | Default | Description |
|---|---:|---|
| `profile_path` | configured `selenium_profile` directory | Browser profile location |
| `headless` | `False` | Run in headless mode |
| `browser` | `"chrome"` | `"chrome"` or `"edge"` |
| `use_undetected` | `False` | Use optional undetected-chromedriver integration |
| `use_stealth_wrapper` | `False` | Return an optional `StealthBot` instance |
| `success_criteria` | `None` | Text passed to `StealthBot` |
| `proxy` | `None` | Proxy passed to `StealthBot` |

## Configuration

| Environment variable | Effect |
|---|---|
| `TELEPORT_ENCRYPTION_KEY` | Fernet key used when encryption is explicitly enabled |
| `TELEPORT_VALIDATE_EXPIRY` | Enable or disable cookie-expiry validation |
| `TELEPORT_VALIDATE_DOMAIN` | Enable or disable source/destination validation |
| `TELEPORT_ALLOWED_DOMAINS` | Comma-separated root-domain allowlist |
| `TELEPORT_BLOCKED_DOMAINS` | Comma-separated root-domain blocklist |
| `TELEPORT_PROFILE_PATH` | Default browser-profile directory |
| `TELEPORT_LOG_LEVEL` | Configured log level value |

Configuration can also be supplied with `TeleportConfig` and `set_config()`.

```python
from selenium_teleport import TeleportConfig, set_config

set_config(
    TeleportConfig(
        validate_expiry=True,
        validate_domain=True,
        allowed_domains=["example.com"],
    )
)
```

## Exceptions

All package exceptions inherit from `TeleportError`. Common subclasses include:

- `SecurityError`, `DomainMismatchError`, `PathTraversalError`, and `SSRFError`
- `EncryptionError`
- `StateFileNotFoundError`, `InvalidStateError`, and `ExpiredSessionError`
- `DriverError` and `DriverNotFoundError`

## Security guidance

- Do not commit state files, browser profiles, encryption keys, screenshots, or saved cookies.
- Use a dedicated, least-privileged test account.
- Restrict state-file permissions and lifecycle outside the library.
- Rotate or revoke sessions if a state file may have been exposed.
- Validate application-specific success after restore; navigation alone does not prove authentication.

## Development

```bash
pip install -e .[dev,security]
pytest tests/ -v
black --check selenium_teleport/ tests/
isort --check-only selenium_teleport/ tests/
mypy selenium_teleport/ --ignore-missing-imports
python -m build
```

## Author

**Dhiraj Das** — [dhirajdas.dev](https://www.dhirajdas.dev)

## License

MIT License. See [LICENSE](LICENSE).
