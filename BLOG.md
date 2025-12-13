# Selenium Teleport: Skip Login Screens Forever

**The 30-second solution to authentication in browser automation that actually works.**

---

## The Hidden Cost of Login

Every test automation engineer knows the pain. You've built the perfect test suite, but 40% of your execution time is spent logging in. Worse, repeated logins trigger bot detection, flag your test accounts, and make your CI pipelines flaky.

The naive solution? "Just save the cookies!"

But if you've tried it, you know it doesn't work.

## Why Cookie-Only Solutions Fail

Here's what most developers miss:

### 1. Modern Apps Don't Just Use Cookies

That React dashboard you're testing? It stores authentication tokens in `localStorage`. That checkout flow? It caches cart data in `sessionStorage`. Saving cookies alone captures maybe 30% of what you need.

### 2. The Same-Origin Policy Blocks You

Try this:
```python
driver.get("about:blank")
driver.add_cookie({"name": "session", "value": "abc123", "domain": "example.com"})
# ❌ InvalidCookieDomainException
```

You *can't* set a cookie for `example.com` while on `about:blank`. Chrome's security model prevents it. Most tutorials skip this entirely.

### 3. The Bot Detection Spiral

Login 50 times a day from the same IP? Congrats, you're now flagged as suspicious. Google will throw CAPTCHAs. Cloudflare will block you. Your test account gets locked.

## The Teleportation Pattern

Selenium Teleport solves all three problems with a simple pattern:

```
1. CAPTURE: Save cookies + localStorage + sessionStorage
2. NAVIGATE: Go to the base domain first (satisfies Same-Origin)
3. INJECT: Add all stored state
4. TELEPORT: Navigate to your target URL — already authenticated
```

It's not magic. It's just doing things in the right order.

## Real-World Usage

### Standard Mode

```python
from selenium_teleport import create_driver, Teleport

driver = create_driver(profile_path="my_sessions")

with Teleport(driver, "hn_session.json") as t:
    if t.has_state():
        # Skip login entirely
        t.load("https://news.ycombinator.com")
    else:
        # First run: login manually or via script
        driver.get("https://news.ycombinator.com/login")
        # ... login process ...
    
    # Your actual test code
    assert "ycombinator" in driver.current_url
# State auto-saved on exit

driver.quit()
```

**First run**: Login once.  
**Every run after**: Instant authentication.

### Stealth Mode

For sites with bot detection (Cloudflare, DataDome, etc.):

```python
from sb_stealth_wrapper import StealthBot
from selenium_teleport import save_state_stealth, load_state_stealth
import os

with StealthBot() as bot:
    if os.path.exists("hn_session.json"):
        load_state_stealth(bot, "hn_session.json", "https://news.ycombinator.com")
    else:
        bot.safe_get("https://news.ycombinator.com/login")
        # Login...
    
    save_state_stealth(bot, "hn_session.json")
```

The `*_stealth` functions use SeleniumBase's stable connection methods, avoiding the stale driver issues that plague naive implementations.

## What Gets Captured

| Storage Type | What's Inside | Persistence |
|-------------|---------------|-------------|
| **Cookies** | Session tokens, CSRF tokens, preferences | Per-domain, can expire |
| **localStorage** | Auth tokens (JWTs), user preferences, cached data | Permanent until cleared |
| **sessionStorage** | Tab-specific state, form data, navigation history | Until tab closes |
| **IndexedDB** (metadata) | Database info used by PWAs | Permanent |

Selenium Teleport captures all of these, not just cookies.

## The Secret Sauce: Base Domain Navigation

Here's the critical insight most miss:

```python
# ❌ This fails
driver.get("about:blank")
driver.add_cookie(my_cookie)  # InvalidCookieDomainException

# ✅ This works
driver.get("https://example.com")  # Navigate first!
driver.add_cookie(my_cookie)  # Now it works
driver.get("https://example.com/dashboard")  # Teleport to destination
```

By navigating to the base domain *before* injecting cookies, we satisfy the Same-Origin Policy. Selenium Teleport does this automatically.

## When to Use This

✅ **Perfect for:**
- E2E test suites with authenticated flows
- Checkout/purchase flow testing
- Dashboard and admin panel automation
- Any multi-page workflow behind login

⚠️ **Keep in mind:**
- Session tokens expire (re-login periodically)
- Some sites use server-side session validation
- Highly secure sites may require additional measures

## Installation

```bash
pip install selenium-teleport

# For sites with bot detection
pip install selenium-teleport[stealth]
```

## The Bigger Picture

Selenium Teleport isn't just about saving time. It's about:

1. **Reliability**: Fewer login attempts = fewer CAPTCHAs = fewer flaky tests
2. **Speed**: Skip the 5-10 second login flow on every test
3. **Focus**: Test your actual feature, not the login page

Your CI/CD pipeline shouldn't spend 40% of its time typing passwords.

---

## Try It

```bash
pip install selenium-teleport
```

**GitHub**: [github.com/godhiraj-code/selenium-teleport](https://github.com/godhiraj-code/selenium-teleport)  
**PyPI**: [pypi.org/project/selenium-teleport](https://pypi.org/project/selenium-teleport/)

---

*Built by [Dhiraj Das](https://dhirajdas.dev) — Automation engineer who got tired of watching tests type passwords.*
