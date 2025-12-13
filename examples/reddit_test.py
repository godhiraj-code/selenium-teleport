"""
Reddit Test with sb-stealth-wrapper

Tests cookie/state persistence on Reddit.

Usage:
    python reddit_test.py
    
    First run: Login to Reddit, then press Enter to save state
    Second run: Should stay logged in automatically!
"""

import sys
import time
import os
import json
from datetime import datetime


def main():
    print("=" * 60)
    print("Selenium Teleport - Reddit Test")
    print("🛡️  Using sb-stealth-wrapper")
    print("=" * 60)
    print()
    
    from sb_stealth_wrapper import StealthBot
    
    state_file = "reddit_state.json"
    
    print("🚀 Starting StealthBot...")
    bot = StealthBot(headless=False)
    bot.__enter__()
    
    driver = bot.sb.driver
    
    # Start background cookie capture immediately
    import threading
    captured_cookies = {"data": [], "count": 0}
    stop_capture = threading.Event()
    
    def capture_loop():
        while not stop_capture.is_set():
            try:
                cookies = driver.get_cookies()
                if cookies:
                    captured_cookies["data"] = cookies
                    captured_cookies["count"] = len(cookies)
            except:
                pass
            time.sleep(1)
    
    capture_thread = threading.Thread(target=capture_loop, daemon=True)
    capture_thread.start()
    
    try:
        # Check for existing state
        if os.path.exists(state_file):
            print("📂 Found saved session! Restoring...")
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            cookies = state.get('cookies', [])
            print(f"   Found {len(cookies)} saved cookies")
            
            # Navigate to Reddit first
            bot.safe_get("https://www.reddit.com")
            time.sleep(2)
            
            # Inject cookies
            injected = 0
            for cookie in cookies:
                try:
                    clean = {k: v for k, v in cookie.items() 
                            if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly']}
                    if 'expiry' in cookie:
                        clean['expiry'] = int(cookie['expiry'])
                    driver.add_cookie(clean)
                    injected += 1
                except:
                    pass
            
            print(f"   Injected {injected} cookies")
            
            # Reload to apply
            driver.refresh()
            time.sleep(3)
            print("✅ Cookies injected! Check if you're logged in.")
        else:
            print("📝 First run - Opening Reddit...")
            bot.safe_get("https://www.reddit.com")
            time.sleep(3)
        
        # Show current URL
        try:
            print(f"📍 Current URL: {driver.current_url[:60]}...")
        except:
            pass
        
        print()
        print("=" * 60)
        print("📋 INSTRUCTIONS:")
        print("   1. Login to Reddit in the browser (if not already)")
        print("   2. Once you're logged in (see your username), come back")
        print("   3. Press ENTER to save your session")
        print("=" * 60)
        print()
        
        # Wait a bit to accumulate cookies
        time.sleep(3)
        print(f"🔄 Background capture: {captured_cookies['count']} cookies so far")
        
        input("\n>>> Press ENTER when logged in to save state... ")
        
        # Stop background capture
        stop_capture.set()
        time.sleep(0.5)
        
        print()
        print("💾 Saving state...")
        
        # Try to get final cookies
        final_cookies = None
        try:
            final_cookies = driver.get_cookies()
            print(f"   Final capture: {len(final_cookies)} cookies")
        except:
            print("   Final capture failed, using background data")
            final_cookies = captured_cookies["data"]
        
        if not final_cookies:
            final_cookies = captured_cookies["data"]
        
        if final_cookies:
            state = {
                'metadata': {
                    'saved_at': datetime.utcnow().isoformat(),
                    'site': 'reddit.com',
                },
                'cookies': final_cookies,
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"✅ Saved {len(final_cookies)} cookies to {state_file}")
            print()
            print("🎊 SUCCESS! Run this script again to test restore!")
        else:
            print("❌ No cookies captured!")
        
        print()
        print("⏳ Closing in 2 seconds...")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\n⚠️ Cancelled!")
        if captured_cookies["data"]:
            print("💾 Saving captured cookies...")
            state = {
                'metadata': {'saved_at': datetime.utcnow().isoformat()},
                'cookies': captured_cookies["data"],
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"✅ Saved {len(captured_cookies['data'])} cookies")
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
