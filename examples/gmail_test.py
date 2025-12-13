"""
Gmail Test with sb-stealth-wrapper

Uses SeleniumBase's built-in cookie methods for state persistence.

Note: Gmail uses complex authentication that may not persist with cookies alone.
This is an experimental example.

Usage:
    python gmail_test.py --stealth
    
    First run: Login to Gmail, then press Enter to save state
    Second run: May or may not restore session (depends on Google's auth)
"""

import sys
import time
import os


def main():
    use_stealth = "--stealth" in sys.argv
    
    print("=" * 60)
    print("Selenium Teleport - Gmail Test")
    if use_stealth:
        print("🛡️  Using sb-stealth-wrapper")
    print("=" * 60)
    print()
    
    if use_stealth:
        _run_gmail_stealth()
    else:
        _run_gmail_standard()


def _run_gmail_standard():
    """Run Gmail test with standard undetected-chromedriver."""
    from selenium_teleport import create_driver, Teleport
    
    driver = create_driver(profile_path="gmail_profile")
    
    try:
        with Teleport(driver, "gmail_state.json") as teleport:
            if teleport.has_state():
                print("🚀 Teleporting to Gmail inbox...")
                teleport.load("https://mail.google.com/mail/u/0/#inbox")
            else:
                print("📝 First run - Opening Gmail...")
                driver.get("https://mail.google.com")
            
            time.sleep(3)
            print(f"📍 Current URL: {driver.current_url}")
            print("Press Ctrl+C to save and exit.")
            
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        driver.quit()
        print("✅ Done!")


def _run_gmail_stealth():
    """
    Run Gmail test with StealthBot using SeleniumBase cookie methods.
    """
    from sb_stealth_wrapper import StealthBot
    
    # Cookie file name (SeleniumBase saves to saved_cookies/<name>.txt)
    cookie_name = "gmail_session"
    cookie_file_path = os.path.join("saved_cookies", f"{cookie_name}.txt")
    
    print("🚀 Starting StealthBot...")
    bot = StealthBot(headless=False)
    bot.__enter__()
    
    try:
        # Navigate to Gmail first
        print("📝 Opening Gmail...")
        bot.safe_get("https://mail.google.com")
        time.sleep(2)
        
        # Check for existing cookies and restore
        if os.path.exists(cookie_file_path):
            print(f"📂 Found saved cookies!")
            print("   Loading cookies...")
            try:
                bot.sb.load_cookies(name=cookie_name)
                print("   ✅ Cookies loaded! Refreshing...")
                bot.sb.refresh()
                time.sleep(3)
                print("✅ Session restored!")
            except Exception as e:
                print(f"⚠️ Restore failed: {e}")
        else:
            print("📝 No saved cookies - first run")
        
        # Show current cookies
        try:
            current_cookies = bot.sb.get_cookies()
            print(f"📊 Current cookies: {len(current_cookies)}")
        except:
            pass
        
        # Get current URL
        try:
            url = bot.sb.get_current_url()
            print(f"📍 URL: {url[:60]}...")
        except:
            pass
        
        print()
        print("=" * 60)
        print("📋 INSTRUCTIONS:")
        print("   1. Check if you're logged in (see your Gmail inbox)")
        print("   2. If not, login to Gmail")
        print("   3. Press ENTER to save cookies")
        print("=" * 60)
        print()
        
        input(">>> Press ENTER to save cookies... ")
        
        print()
        print("💾 Saving cookies...")
        
        try:
            cookies = bot.sb.get_cookies()
            print(f"   Found {len(cookies)} cookies")
            
            bot.sb.save_cookies(name=cookie_name)
            
            if os.path.exists(cookie_file_path):
                print(f"✅ Cookies saved to {cookie_file_path}")
                print()
                print("🎊 SUCCESS! Run again with --stealth to test restore!")
            else:
                print("⚠️ Cookie file not found at expected path")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("⏳ Closing in 3 seconds...")
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n⚠️ Cancelled!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Closing browser...")
        try:
            bot.__exit__(None, None, None)
        except:
            pass
        print("✅ Done!")


if __name__ == "__main__":
    main()
