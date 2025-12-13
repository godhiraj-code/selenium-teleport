"""Debug cookie access on a site that definitely has cookies."""
from sb_stealth_wrapper import StealthBot
import time

print("Starting StealthBot...")
bot = StealthBot(headless=False)
bot.__enter__()

try:
    # Use Google which definitely sets cookies
    print("\nNavigating to google.com (definitely has cookies)...")
    bot.safe_get("https://www.google.com")
    time.sleep(3)
    
    print("\nTrying to get cookies...")
    
    # Method 1: SeleniumBase get_cookies
    try:
        cookies1 = bot.sb.get_cookies()
        print(f"1. bot.sb.get_cookies(): {len(cookies1)} cookies")
        if cookies1:
            for c in cookies1[:5]:
                print(f"   - {c.get('name', c) if isinstance(c, dict) else c}")
    except Exception as e:
        print(f"1. bot.sb.get_cookies() FAILED: {e}")
    
    # Method 2: Direct driver access WHILE browser is still connected
    try:
        # Try immediately without delay
        driver = bot.sb.driver
        cookies2 = driver.get_cookies()
        print(f"2. driver.get_cookies(): {len(cookies2)} cookies")
        if cookies2:
            for c in cookies2[:5]:
                print(f"   - {c.get('name')}")
    except Exception as e:
        print(f"2. driver.get_cookies() FAILED: {e}")
    
    # Method 3: SeleniumBase execute_script
    try:
        cookies3 = bot.sb.execute_script("return document.cookie")
        print(f"3. execute_script document.cookie: '{cookies3[:100] if cookies3 else ''}'")
    except Exception as e:
        print(f"3. execute_script FAILED: {e}")
    
    # Method 4: Check if sb has other cookie methods
    print("\n4. Available sb methods containing 'cookie':")
    for m in dir(bot.sb):
        if 'cookie' in m.lower():
            print(f"   - {m}")
    
    print("\nWaiting 5 seconds before closing (cookies should persist)...")
    time.sleep(5)
    
    # Try again after waiting
    print("\nTrying again after wait...")
    try:
        cookies_final = bot.sb.get_cookies()
        print(f"   bot.sb.get_cookies(): {len(cookies_final)} cookies")
    except Exception as e:
        print(f"   FAILED: {e}")

finally:
    print("\nClosing...")
    try:
        bot.__exit__(None, None, None)
    except:
        pass
    print("Done!")
