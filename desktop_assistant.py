import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                            QComboBox, QStatusBar, QSystemTrayIcon, QMenu)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPoint
from PySide6.QtGui import QIcon, QAction, QFont, QPainter, QColor
import pyttsx3
import speech_recognition as sr
import webbrowser
import wikipedia
import requests
import geocoder
import threading
import datetime
import dotenv
import winsound
import pyautogui
import cv2
import numpy as np
from PIL import Image
import pytesseract
from together import Together
import json
import pathlib
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import queue
import keyboard
from browser_agent import BrowserAgent

# Configuration
CONFIG = {
    'SOUND_FILES': {
        'intro': 'sounds/intro.wav',
        'listen': 'sounds/error-2.wav',
        'error': 'sounds/short-beep-tone.wav'
    },
    'TESSERACT_CMD': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    'BUTTON_IMAGES_DIR': 'button_images',
    'SCREENSHOT_DIR': 'screenshots',
    'SEARCH_ENGINES': {
        'google': 'https://www.google.com/search?q=',
        'bing': 'https://www.bing.com/search?q=',
        'duckduckgo': 'https://duckduckgo.com/?q='
    },
    'MAX_SEARCH_RESULTS': 5
}

# Initialize Together API client
dotenv.load_dotenv()
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', "f15ba22ed0665375913552d87afef7ddef0ba28cfe2ff8976d6ce81e92ad4450")
client = Together()
client.api_key = TOGETHER_API_KEY

# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = CONFIG['TESSERACT_CMD']

# Initialize webdriver
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

class StatusIndicator(QWidget):
    """Global status indicator showing if assistant is listening"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(20, 20)
        
        # Position in bottom-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 30, screen.height() - 30)
        
        self.is_listening = False
        self.show()
        
    def paintEvent(self, event):
        if self.is_listening:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 255, 0, 180))  # Semi-transparent green
            painter.drawEllipse(0, 0, 20, 20)
            
    def set_listening(self, listening):
        self.is_listening = listening
        self.update()
        self.setVisible(listening)

class VoiceThread(QThread):
    """Thread for handling voice input"""
    text_received = Signal(str)
    status_update = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        self.recognizer = sr.Recognizer()
        self.mic_active = True
        self.stop_listening = False
        self.mic_queue = queue.Queue()
        self.is_running = False
        
    def run(self):
        self.is_running = True
        while not self.stop_listening and self.is_running:
            try:
                with sr.Microphone() as source:
                    self.status_update.emit("Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    self.status_update.emit("Ready to listen")
                    
                    while not self.stop_listening and self.is_running:
                        if self.mic_active:
                            try:
                                self.status_update.emit("Listening...")
                                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=None)
                                
                                try:
                                    query = self.recognizer.recognize_google(audio)
                                    if query.strip():
                                        self.text_received.emit(query.lower())
                                except sr.UnknownValueError:
                                    pass
                                except sr.RequestError as e:
                                    self.status_update.emit(f"Error: {str(e)}")
                            except Exception as e:
                                if "listening timed out" not in str(e):
                                    self.status_update.emit(f"Error: {str(e)}")
                                continue
            except Exception as e:
                self.status_update.emit(f"Microphone error: {str(e)}")
                time.sleep(2)
                continue

    def toggle_microphone(self):
        self.mic_active = not self.mic_active
        status = "ON" if self.mic_active else "OFF"
        self.status_update.emit(f"Microphone {status}")
        winsound.Beep(1000 if self.mic_active else 500, 100)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self):
        self.stop_listening = True
        self.is_running = False
        self.wait()

class AssistantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAGE Desktop Assistant")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize browser agent
        self.browser_agent = BrowserAgent(persistent_session=False)
        
        # Create status indicator
        self.status_indicator = StatusIndicator()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_assistant)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Microphone toggle button
        self.mic_button = QPushButton("🎤 Toggle Microphone")
        self.mic_button.clicked.connect(self.toggle_microphone)
        controls_layout.addWidget(self.mic_button)
        
        # Browser toggle button
        self.browser_button = QPushButton("🌐 Toggle Browser")
        self.browser_button.clicked.connect(self.toggle_browser)
        controls_layout.addWidget(self.browser_button)
        
        # Voice command dropdown
        self.command_dropdown = QComboBox()
        self.command_dropdown.addItems([
            "Analyze Screen",
            "Click Button",
            "Search Web",
            "Get Weather",
            "Tell Joke",
            "Get Time",
            "Browse Website",
            "Take Screenshot"
        ])
        controls_layout.addWidget(self.command_dropdown)
        
        # Execute button
        self.execute_button = QPushButton("▶️ Execute")
        self.execute_button.clicked.connect(self.execute_command)
        controls_layout.addWidget(self.execute_button)
        
        layout.addLayout(controls_layout)
        
        # Create chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Arial", 10))
        layout.addWidget(self.chat_display)
        
        # Initialize voice thread
        self.voice_thread = VoiceThread()
        self.voice_thread.text_received.connect(self.process_voice_input)
        self.voice_thread.status_update.connect(self.update_status)
        self.voice_thread.start()
        
        # Register keyboard shortcuts
        keyboard.on_press_key('m', lambda _: self.toggle_microphone())
        keyboard.on_press_key('q', lambda _: self.quit_assistant())
        keyboard.on_press_key('b', lambda _: self.toggle_browser())
        
        # Register Win+Alt hotkey
        keyboard.add_hotkey('windows+alt', self.toggle_assistant)
        
        # Initialize assistant state
        self.assistant_active = False
        self.browser_active = False
        
        # Add welcome message
        self.add_message("SAGE Desktop Assistant", "system")
        self.add_message("Press Win+Alt to activate/deactivate the assistant", "system")
        self.add_message("Press 'M' to toggle microphone", "system")
        self.add_message("Press 'B' to toggle browser", "system")
        self.add_message("Press 'Q' to quit", "system")
        
    def add_message(self, text, sender="user"):
        """Add a message to the chat display"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "🤖 SAGE:" if sender == "assistant" else "👤 You:"
        self.chat_display.append(f"[{timestamp}] {prefix} {text}")
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        
    def update_status(self, message):
        """Update the status bar with a message"""
        self.statusBar.showMessage(message)
        
    def toggle_microphone(self):
        """Toggle the microphone on/off"""
        self.voice_thread.toggle_microphone()
        self.status_indicator.set_listening(self.voice_thread.mic_active and self.assistant_active)
        
    def toggle_assistant(self):
        """Toggle the assistant active state"""
        self.assistant_active = not self.assistant_active
        status = "activated" if self.assistant_active else "deactivated"
        self.add_message(f"Assistant {status}", "system")
        self.voice_thread.speak(f"Assistant {status}")
        self.status_indicator.set_listening(self.voice_thread.mic_active and self.assistant_active)
        
    def toggle_browser(self):
        """Toggle browser on/off"""
        self.browser_active = not self.browser_active
        if self.browser_active:
            if self.browser_agent.start_browser():
                self.add_message("Browser activated", "system")
                self.browser_button.setText("🌐 Close Browser")
            else:
                self.browser_active = False
                self.add_message("Failed to start browser", "system")
        else:
            if self.browser_agent.close_browser():
                self.add_message("Browser deactivated", "system")
                self.browser_button.setText("🌐 Toggle Browser")
            else:
                self.add_message("Failed to close browser", "system")
                
    def process_voice_input(self, text):
        """Process voice input"""
        self.add_message(text)
        
        if not self.assistant_active:
            self.add_message("Press Win+Alt to activate the assistant", "assistant")
            return
            
        # Process commands
        self.process_command(text)
        
    def process_command(self, command):
        """Process user commands"""
        try:
            if "browse" in command.lower() or "open website" in command.lower():
                # Extract URL from command
                url = command.lower().split("browse")[-1].strip() if "browse" in command.lower() else command.lower().split("open website")[-1].strip()
                if not url.startswith("http"):
                    url = "https://" + url
                if self.browser_agent.navigate(url):
                    self.add_message(f"Navigating to {url}", "assistant")
                else:
                    self.add_message("Failed to navigate to website", "assistant")
                    
            elif "click" in command.lower() and "button" in command.lower():
                button_text = command.split("click")[-1].split("button")[-1].strip()
                if self.browser_agent.click_element(f"text={button_text}"):
                    self.add_message(f"Clicked {button_text} button", "assistant")
                else:
                    self.add_message(f"Failed to click {button_text} button", "assistant")
                    
            elif "type" in command.lower():
                text = command.split("type")[-1].strip()
                if self.browser_agent.type_text("input", text):
                    self.add_message(f"Typed: {text}", "assistant")
                else:
                    self.add_message("Failed to type text", "assistant")
                    
            elif "screenshot" in command.lower():
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"screenshots/screenshot_{timestamp}.png"
                os.makedirs("screenshots", exist_ok=True)
                if self.browser_agent.take_screenshot(path):
                    self.add_message(f"Screenshot saved to {path}", "assistant")
                else:
                    self.add_message("Failed to take screenshot", "assistant")
                    
            elif "what's on my screen" in command or "describe my screen" in command:
                self.add_message("Analyzing screen...", "assistant")
                screen_text = self.get_screen_text()
                response = self.get_llm_response(f"Based on this screen content: {screen_text}")
                self.add_message(response, "assistant")
                self.voice_thread.speak(response)
                
            elif "weather" in command:
                location = geocoder.ip('me')
                city = location.city
                self.add_message(f"Getting weather for: {city}", "assistant")
                weather_report = self.get_weather(city)
                self.add_message(weather_report, "assistant")
                self.voice_thread.speak(weather_report)
                
            elif "tell me a joke" in command:
                self.add_message("Fetching a joke...", "assistant")
                joke = requests.get("https://official-joke-api.appspot.com/random_joke").json()
                self.add_message(joke['setup'], "assistant")
                self.add_message(joke['punchline'], "assistant")
                self.voice_thread.speak(f"{joke['setup']} {joke['punchline']}")
                
            elif "time" in command:
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                self.add_message(f"The time is {current_time}", "assistant")
                self.voice_thread.speak(f"The time is {current_time}")
                
            else:
                # Use LLM for general queries
                self.add_message("Processing with AI...", "assistant")
                response = self.get_llm_response(command)
                self.add_message(response, "assistant")
                self.voice_thread.speak(response)
                
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.add_message(error_msg, "assistant")
            self.voice_thread.speak("I encountered an error while processing your request.")
            
    def execute_command(self):
        """Execute the selected command from the dropdown"""
        command = self.command_dropdown.currentText()
        if command == "Analyze Screen":
            self.process_command("what's on my screen")
        elif command == "Click Button":
            self.process_command("click button")
        elif command == "Search Web":
            self.process_command("search web for")
        elif command == "Get Weather":
            self.process_command("weather")
        elif command == "Tell Joke":
            self.process_command("tell me a joke")
        elif command == "Get Time":
            self.process_command("time")
        elif command == "Browse Website":
            self.process_command("browse")
        elif command == "Take Screenshot":
            self.process_command("screenshot")
            
    def get_screen_text(self):
        """Capture screen and extract text using OCR"""
        try:
            screenshot = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            text = pytesseract.image_to_string(thresh, config='--psm 6')
            return text.strip()
        except Exception as e:
            return f"Error capturing screen: {str(e)}"
            
    def get_weather(self, city_name):
        """Get weather information for a city"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
            response = requests.get(url)
            data = response.json()
            if response.status_code == 200:
                weather_description = data['weather'][0]['description']
                temperature = data['main']['temp']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']
                return f"The weather in {city_name} is {weather_description}. Temperature: {temperature}°C, Humidity: {humidity}%, Wind Speed: {wind_speed} m/s"
            else:
                return "Failed to fetch weather data"
        except Exception as e:
            return f"Error getting weather: {str(e)}"
            
    def get_llm_response(self, query, use_web_search=False):
        """Get response from LLM (temporarily disabled)"""
        return "I apologize, but the AI service is currently unavailable. Basic voice commands are still working!"
            
    def web_search(self, query, engine='google', max_results=5):
        """Perform web search"""
        try:
            search_url = CONFIG['SEARCH_ENGINES'][engine] + query.replace(' ', '+')
            driver.get(search_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g" if engine == 'google' else "li.b_algo"))
            )
            
            results = []
            if engine == 'google':
                elements = driver.find_elements(By.CSS_SELECTOR, "div.g")[:max_results]
                for element in elements:
                    try:
                        title = element.find_element(By.CSS_SELECTOR, "h3").text
                        link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        snippet = element.find_element(By.CSS_SELECTOR, "div.VwiC3b").text
                        results.append({"title": title, "link": link, "snippet": snippet})
                    except:
                        continue
            return results
        except Exception as e:
            return []
            
    def quit_assistant(self):
        """Clean up and quit the application"""
        self.voice_thread.stop()
        self.voice_thread.wait()
        if self.browser_active:
            self.browser_agent.close_browser()
        try:
            driver.quit()
        except:
            pass
        self.status_indicator.close()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = AssistantWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 