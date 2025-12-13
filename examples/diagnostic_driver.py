"""
Diagnostic: Test driver stability with StealthBot
"""

import time
from sb_stealth_wrapper import StealthBot


def test_driver_access():
    print("Testing StealthBot driver access...")
    
    # Use proper context manager
    with StealthBot(headless=False) as bot:
        print(f"1. bot type: {type(bot)}")
        print(f"2. bot.sb type: {type(bot.sb)}")
        print(f"3. bot.sb.driver type: {type(bot.sb.driver)}")
        
        # Navigate
        bot.safe_get("https://example.com")
        time.sleep(2)
        
        # Test via bot.sb methods
        print("\n--- Via bot.sb methods ---")
        try:
            cookies1 = bot.sb.get_cookies()
            print(f"bot.sb.get_cookies(): {len(cookies1)} cookies")
        except Exception as e:
            print(f"bot.sb.get_cookies() FAILED: {e}")
        
        # Test via bot.sb.driver directly
        print("\n--- Via bot.sb.driver ---")
        try:
            cookies2 = bot.sb.driver.get_cookies()
            print(f"bot.sb.driver.get_cookies(): {len(cookies2)} cookies")
        except Exception as e:
            print(f"bot.sb.driver.get_cookies() FAILED: {e}")
        
        # Test execute_script
        print("\n--- Via execute_script ---")
        try:
            local_storage = bot.sb.driver.execute_script("""
                var data = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
            """)
            print(f"localStorage via driver: {len(local_storage or {})} items")
        except Exception as e:
            print(f"execute_script FAILED: {e}")
        
        # Test SeleniumBase execute_script
        try:
            local_storage2 = bot.sb.execute_script("""
                var data = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
            """)
            print(f"localStorage via bot.sb: {len(local_storage2 or {})} items")
        except Exception as e:
            print(f"bot.sb.execute_script FAILED: {e}")
        
        print("\n✅ All tests completed inside context manager")
    
    print("\n✅ Exited context manager cleanly")


if __name__ == "__main__":
    test_driver_access()
