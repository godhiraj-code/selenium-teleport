"""
Test the new save_state_stealth/load_state_stealth functions.

These functions use bot.sb methods which maintain a stable connection
even after navigation with challenge handling.

Usage:
    python test_stealth_state.py
    
    First run: Login to HN, press Enter to save full state
    Second run: Should restore Cookies + LocalStorage + SessionStorage
"""

import time
import os
from selenium_teleport import save_state_stealth, load_state_stealth


def main():
    print("=" * 60)
    print("Selenium Teleport - StealthBot State Test")
    print("Testing: save_state_stealth / load_state_stealth")
    print("=" * 60)
    print()
    
    from sb_stealth_wrapper import StealthBot
    
    state_file = "hn_stealth_state.json"
    
    print("🚀 Starting StealthBot...")
    
    with StealthBot(headless=False) as bot:
        
        # Check for existing state
        if os.path.exists(state_file):
            print("📂 Found saved state!")
            print("   Loading with load_state_stealth...")
            
            try:
                state = load_state_stealth(bot, state_file, "https://news.ycombinator.com")
                print(f"   ✅ Loaded: {len(state.get('cookies', []))} cookies, "
                      f"{len(state.get('localStorage', {}))} localStorage, "
                      f"{len(state.get('sessionStorage', {}))} sessionStorage")
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Load failed: {e}")
                import traceback
                traceback.print_exc()
                bot.safe_get("https://news.ycombinator.com")
        else:
            print("📝 No saved state - first run")
            bot.safe_get("https://news.ycombinator.com")
            time.sleep(2)
        
        # Show current storage using bot.sb methods
        print()
        print("📊 Current browser storage:")
        try:
            cookies = bot.sb.get_cookies()
            print(f"   Cookies: {len(cookies)}")
            
            local_storage = bot.sb.execute_script("""
                var data = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
            """) or {}
            print(f"   LocalStorage: {len(local_storage)} items")
            
            session_storage = bot.sb.execute_script("""
                var data = {};
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    data[key] = sessionStorage.getItem(key);
                }
                return data;
            """) or {}
            print(f"   SessionStorage: {len(session_storage)} items")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print()
        print("=" * 60)
        print("📋 INSTRUCTIONS:")
        print("   1. Check if you're logged in (see your username)")
        print("   2. If not, login to HN")
        print("   3. Press ENTER to save FULL state")
        print("=" * 60)
        print()
        
        input(">>> Press ENTER to save full state... ")
        
        print()
        print("💾 Saving with save_state_stealth...")
        
        try:
            state = save_state_stealth(bot, state_file)
            print(f"✅ Saved to {state_file}:")
            print(f"   - {len(state.get('cookies', []))} cookies")
            print(f"   - {len(state.get('localStorage', {}))} localStorage items")
            print(f"   - {len(state.get('sessionStorage', {}))} sessionStorage items")
            print()
            print("🎊 SUCCESS! Run again to test restore!")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        print("⏳ Closing in 3 seconds...")
        time.sleep(3)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
