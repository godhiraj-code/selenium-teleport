"""
Example: Save and load browser state with Selenium Teleport.

This example demonstrates the basic workflow:
1. Login to a website
2. Save the authenticated state
3. Restore the state in a new browser session
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium_teleport import save_state, load_state, Teleport


def example_save_state():
    """Example: Save state after login."""
    driver = webdriver.Chrome()
    
    try:
        # Navigate to login page
        driver.get("https://your-app.com/login")
        
        # Perform login
        driver.find_element(By.ID, "username").send_keys("your_username")
        driver.find_element(By.ID, "password").send_keys("your_password")
        driver.find_element(By.ID, "login-button").click()
        
        # Wait for login to complete
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Save the authenticated state
        save_state(driver, "my_session.json")
        print("✅ State saved successfully!")
        
    finally:
        driver.quit()


def example_load_state():
    """Example: Load state and teleport to authenticated page."""
    driver = webdriver.Chrome()
    
    try:
        # Teleport directly to a protected page
        load_state(driver, "my_session.json", "https://your-app.com/dashboard")
        
        # You're now logged in!
        print(f"✅ Teleported! Current page: {driver.title}")
        
        # Continue with your automation...
        
    finally:
        driver.quit()


def example_context_manager():
    """Example: Use Teleport context manager for automatic state management."""
    driver = webdriver.Chrome()
    
    try:
        with Teleport(driver, "my_session.json") as teleport:
            if teleport.has_state():
                # Existing state found - teleport directly
                teleport.load("https://your-app.com/dashboard")
                print("✅ Teleported using saved state!")
            else:
                # No state - need to login first
                driver.get("https://your-app.com/login")
                print("📝 No saved state. Please login...")
                
                # Perform login...
                driver.find_element(By.ID, "username").send_keys("your_username")
                driver.find_element(By.ID, "password").send_keys("your_password")
                driver.find_element(By.ID, "login-button").click()
                
                WebDriverWait(driver, 10).until(
                    EC.url_contains("/dashboard")
                )
            
            # Run your tests here...
            print(f"Current page: {driver.title}")
            
        # State is automatically saved on successful exit
        print("✅ State auto-saved on exit!")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example.py [save|load|auto]")
        print("  save - Login and save state")
        print("  load - Load state and teleport")
        print("  auto - Use context manager (auto-detects state)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "save":
        example_save_state()
    elif command == "load":
        example_load_state()
    elif command == "auto":
        example_context_manager()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
