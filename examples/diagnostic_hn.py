"""
Diagnostic: Test driver stability after HN navigation with challenges.
"""

import time
from sb_stealth_wrapper import StealthBot


def test_hn_navigation():
    print("Testing driver stability on HN...")
    
    with StealthBot(headless=False) as bot:
        print(f"1. Initial driver: {type(bot.sb.driver)}")
        print(f"   Driver session id: {bot.sb.driver.session_id}")
        
        # Navigate to HN (may trigger challenge handling)
        print("\n2. Navigating to HN...")
        bot.safe_get("https://news.ycombinator.com")
        
        print("\n3. After navigation:")
        print(f"   Driver type: {type(bot.sb.driver)}")
        print(f"   Driver session id: {bot.sb.driver.session_id}")
        
        # Wait a moment
        time.sleep(2)
        
        # Try to get fresh driver reference
        print("\n4. Trying fresh driver reference...")
        driver = bot.sb.driver
        print(f"   Fresh driver: {type(driver)}")
        
        print("\n5. Testing operations with fresh reference:")
        try:
            cookies = driver.get_cookies()
            print(f"   get_cookies(): {len(cookies)} cookies ✅")
        except Exception as e:
            print(f"   get_cookies() FAILED: {e}")
        
        try:
            url = driver.current_url
            print(f"   current_url: {url[:50]}... ✅")
        except Exception as e:
            print(f"   current_url FAILED: {e}")
        
        try:
            ls = driver.execute_script("return Object.keys(localStorage).length")
            print(f"   localStorage keys: {ls} ✅")
        except Exception as e:
            print(f"   execute_script FAILED: {e}")
        
        print("\n6. Trying via bot.sb methods:")
        try:
            cookies2 = bot.sb.get_cookies()
            print(f"   bot.sb.get_cookies(): {len(cookies2)} cookies ✅")
        except Exception as e:
            print(f"   bot.sb.get_cookies() FAILED: {e}")
        
        try:
            url2 = bot.sb.get_current_url()
            print(f"   bot.sb.get_current_url(): {url2[:50]}... ✅")
        except Exception as e:
            print(f"   bot.sb.get_current_url() FAILED: {e}")
        
        print("\n✅ Tests complete")
    
    print("\n✅ Exited context manager")


if __name__ == "__main__":
    test_hn_navigation()
