# 🚀 Selenium Teleport

**Save and restore browser state (Cookies, LocalStorage, SessionStorage) to instantly skip login screens.**

## 🛑 The Problem
Automating checkouts or complex workflows is hard because **logging in every time is slow and triggers bot detection**.

Most developers try to save cookies, but it fails because:
1.  **Missing Data**: Modern sites use `LocalStorage` and `SessionStorage` for auth tokens, not just cookies.
2.  **Security Blocks**: Trying to inject cookies into a blank tab (`data:,`) fails due to the **Same-Origin Policy**. You can't set a cookie for `example.com` while you are on `about:blank`.
3.  **Bot Detection**: Repeated logins flag your IP/Account as suspicious.

## ✅ The Solution: Teleport
**Selenium Teleport** acts as a universal state bridge.
1.  **Captures Everything**: Saves Cookies, LocalStorage, and SessionStorage.
2.  **Bypasses Security**: Automatically navigates to the site's "Base Domain" first to satisfy the Same-Origin Policy.
3.  **Injects & Teleports**: Safely injects the state and "teleports" the browser to your destination URL, instantly authenticated.

```mermaid
sequenceDiagram
    participant S as Script
    participant B as Browser
    participant F as State File

    %% Save Flow
    Note over S,F: 💾 SAVE SATE
    S->>B: Login manually or via script
    S->>B: Extract Cookies + Local/Session Storage
    B->>F: Save to JSON

    %% Restore Flow
    Note over S,F: 🚀 TELEPORT (Restore)
    S->>B: Open New Browser
    S->>F: Load JSON
    S->>B: 1. Navigate to Base Domain (e.g. example.com)
    Note right of B: Satisfies Same-Origin Policy
    S->>B: 2. Inject Cookies + Storage
    S->>B: 3. Navigate to Dashboard
    Note right of B: ⚡ User is instantly logged in!
```

## ✨ Features

- **Complete State Capture** - Cookies, LocalStorage, SessionStorage
- **Same-Origin Bypass** - Navigates to base domain before injection
- **Anti-Detection** - Optional undetected-chromedriver integration
- **StealthBot Support** - Full integration with sb-stealth-wrapper
- **Context Manager** - Auto-save on successful exit

## 📦 Installation

```bash
pip install selenium-teleport

# For stealth mode (Cloudflare bypass)
pip install selenium-teleport[stealth]
```

## 🏃 Quick Start

### Standard Mode

```python
from selenium_teleport import create_driver, Teleport

driver = create_driver(profile_path="my_profile")

with Teleport(driver, "session.json") as t:
    if t.has_state():
        t.load("https://example.com/dashboard")
    else:
        driver.get("https://example.com/login")
        # Login manually...

driver.quit()
```

### 🛡️ Stealth Mode (sb-stealth-wrapper)

For sites with bot detection. Uses **full state persistence** (Cookies + LocalStorage + SessionStorage):

```python
from sb_stealth_wrapper import StealthBot
from selenium_teleport import save_state_stealth, load_state_stealth
import os

with StealthBot() as bot:
    # Restore state if it exists
    if os.path.exists("state.json"):
        load_state_stealth(bot, "state.json", "https://example.com")
    else:
        bot.safe_get("https://example.com/login")
        # Login...
    
    # Save state for next time
    save_state_stealth(bot, "state.json")
```

**Tested and working**: Hacker News ✅

## 📖 API Reference

### Standard Mode

| Function | Description |
|----------|-------------|
| `save_state(driver, file_path)` | Save Cookies, LocalStorage, SessionStorage to JSON |
| `load_state(driver, file_path, url)` | Load state and navigate to URL |
| `Teleport(driver, file_path)` | Context manager with auto-save |

### Stealth Mode (sb-stealth-wrapper)

| Function | Description |
|----------|-------------|
| `save_state_stealth(bot, file_path)` | Save state using bot.sb methods (stable connection) |
| `load_state_stealth(bot, file_path, url)` | Load state and navigate using bot.sb methods |

### `create_driver(profile_path, headless, use_stealth_wrapper)`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `profile_path` | `"selenium_profile"` | Browser profile location |
| `headless` | `False` | Headless mode |
| `use_stealth_wrapper` | `False` | Use sb-stealth-wrapper |

## ⚠️ Important Notes

1. **Standard mode**: Uses `driver.get_cookies()` / `driver.execute_script()`
2. **Stealth mode**: Uses `bot.sb` methods which maintain stable connection after challenge handling
3. **Session persistence varies by site** - Some sites use complex auth beyond cookies

## 📄 License

MIT License
