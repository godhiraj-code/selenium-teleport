"""
Hacker News Test with sb-stealth-wrapper

Tested and verified to work. Uses SeleniumBase's built-in cookie methods.

Usage:
    python hn_test.py
    
    First run: Login to HN, then press Enter to save state
    Second run: Should stay logged in automatically!
"""

import time
import os


def main():
    print("=" * 60)
    print("Selenium Teleport - Hacker News Test")
    print("🛡️  Using sb-stealth-wrapper")
    print("=" * 60)
    print()
    
    from sb_stealth_wrapper import StealthBot
    
    # SeleniumBase saves cookies to saved_cookies folder
    cookie_name = "hn_session"  # SeleniumBase appends .txt
    cookie_file_path = os.path.join("saved_cookies", f"{cookie_name}.txt")
    
    print("🚀 Starting StealthBot...")
    bot = StealthBot(headless=False)
    bot.__enter__()
    
    try:
        # Navigate to HN first
        print("📝 Opening Hacker News...")
        bot.safe_get("https://news.ycombinator.com")
        time.sleep(2)
        
        # Check for existing cookies and restore
        if os.path.exists(cookie_file_path):
            print(f"📂 Found saved cookies at {cookie_file_path}!")
            print("   Loading cookies...")
            try:
                bot.sb.load_cookies(name=cookie_name)
                print("   ✅ Cookies loaded!")
                # Refresh to apply
                print("   Refreshing page...")
                bot.sb.refresh()
                time.sleep(2)
                print("✅ Cookies restored! Check if you're logged in.")
            except Exception as e:
                print(f"⚠️ Restore failed: {e}")
        else:
            print(f"📝 No saved cookies found at {cookie_file_path}")
            print("   This appears to be your first run.")
        
        # Show current cookies
        try:
            current_cookies = bot.sb.get_cookies()
            print(f"📊 Current cookies: {len(current_cookies)}")
            for c in current_cookies[:3]:
                if isinstance(c, dict):
                    print(f"   - {c.get('name')}")
        except Exception as e:
            print(f"   Cookie check error: {e}")
        
        print()
        print("=" * 60)
        print("📋 INSTRUCTIONS:")
        print("   1. Check if you're already logged in (see your username)")
        print("   2. If not, click 'login' and login to HN")
        print("   3. Press ENTER to save cookies for next time")
        print("=" * 60)
        print()
        
        input(">>> Press ENTER to save cookies... ")
        
        print()
        print("💾 Saving cookies using SeleniumBase...")
        
        try:
            # Show cookies before saving
            cookies = bot.sb.get_cookies()
            print(f"   Found {len(cookies)} cookies")
            
            # SeleniumBase save_cookies - saves to saved_cookies/<name>.txt
            bot.sb.save_cookies(name=cookie_name)
            
            # Verify file was created
            if os.path.exists(cookie_file_path):
                print(f"✅ Cookies saved to {cookie_file_path}")
                print()
                print("🎊 SUCCESS! Run this script again - you should stay logged in!")
            else:
                print(f"⚠️ File not found at expected location: {cookie_file_path}")
                # Check where it actually saved
                if os.path.exists("saved_cookies"):
                    files = os.listdir("saved_cookies")
                    print(f"   Files in saved_cookies/: {files}")
            
        except Exception as e:
            print(f"❌ Failed to save cookies: {e}")
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
