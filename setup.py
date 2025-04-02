from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
import sys
import subprocess

def install_chrome_driver():
    """Install Chrome WebDriver"""
    try:
        print("Installing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.quit()
        print("Chrome WebDriver installed successfully!")
    except Exception as e:
        print(f"Error installing Chrome WebDriver: {str(e)}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    directories = ['sounds', 'button_images', 'screenshots']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def check_tesseract():
    """Check if Tesseract is installed"""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("Tesseract is properly installed!")
    except Exception as e:
        print("Tesseract is not installed or not properly configured.")
        print("Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

def main():
    print("Setting up Voice Assistant...")
    
    # Create directories
    create_directories()
    
    # Check Tesseract
    check_tesseract()
    
    # Install Chrome WebDriver
    install_chrome_driver()
    
    print("\nSetup completed successfully!")
    print("\nPlease make sure to:")
    print("1. Place your sound files in the 'sounds' directory")
    print("2. Create a '.env' file with your API keys")
    print("3. Place button images in the 'button_images' directory if needed")
    print("\nYou can now run the assistant with: python voice_assistant.py")

if __name__ == "__main__":
    main() 