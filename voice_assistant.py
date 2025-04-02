import pyttsx3
import speech_recognition as sr
import webbrowser
import wikipedia
import requests
import geocoder
import threading
import datetime
import os
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

# Global variables for thread control
mic_active = False
mic_queue = queue.Queue()
stop_listening = False
program_status = True  # Add program status flag

# Create necessary directories
for dir_path in [CONFIG['BUTTON_IMAGES_DIR'], CONFIG['SCREENSHOT_DIR']]:
    pathlib.Path(dir_path).mkdir(exist_ok=True)

# Initialize Together API client
dotenv.load_dotenv()
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', "f15ba22ed0665375913552d87afef7ddef0ba28cfe2ff8976d6ce81e92ad4450")
client = Together(api_key=TOGETHER_API_KEY)

# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = CONFIG['TESSERACT_CMD']

# Initialize webdriver
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

engine = pyttsx3.init()
engine.setProperty('rate', 180)
recognizer = sr.Recognizer()

#API keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

# Words
endwords = ["stop", "end", "bye"]
wakewords = "sage"
wiki = ["what is ","what are ","who is ","who are "]
math_terms = ["plus","minus","divided by","into","multiplied by","by","+","-","*","/","x"]
user = "boss"

def play_sound(sound_type):
    """Play sound with error handling"""
    try:
        # Use system beep as fallback
        if sound_type == 'intro':
            winsound.Beep(440, 500)  # 440Hz for 500ms
        elif sound_type == 'listen':
            winsound.Beep(880, 300)  # 880Hz for 300ms
        elif sound_type == 'error':
            winsound.Beep(220, 200)  # 220Hz for 200ms
    except Exception as e:
        print(f"Error playing sound: {str(e)}")

def play_intro():
    play_sound('intro')

def play_listen():
    play_sound('listen')

def play_error():
    play_sound('error')

def print_and_speak(text):
    print(text)
    speak(text)
    
def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("\nListening...")
        play_listen()
        audio = recognizer.listen(source)
        print("Processing")
        try:
            query = recognizer.recognize_google(audio)
            print(f"Query : {query}")
            return query.lower()
        except Exception as e:
            print("Failed to Recognize Audio")
            play_error()
            speak(f"Apologies, could you please repeat that {user}?")
            return listen()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def get_weather(city_name):
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

def evaluate_math_expression(expression):
    try:
        result = eval(expression)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def get_screen_text(region=None):
    """Capture screen and extract text using OCR with error handling"""
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot(region=region)
        
        # Save screenshot for debugging
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(CONFIG['SCREENSHOT_DIR'], f'screenshot_{timestamp}.png')
        screenshot.save(screenshot_path)
        
        # Convert to OpenCV format
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Preprocess image for better OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Perform OCR with multiple configurations
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        
        if not text.strip():
            # Try alternative OCR configuration if no text found
            text = pytesseract.image_to_string(gray, config='--psm 3')
        
        return text.strip()
    except Exception as e:
        print(f"Error in screen capture/OCR: {str(e)}")
        return ""

def find_and_click_button(button_text, confidence=0.8):
    """Find and click a button on screen based on text with improved detection"""
    try:
        # First try to find button by image
        button_path = os.path.join(CONFIG['BUTTON_IMAGES_DIR'], f'button_{button_text}.png')
        if os.path.exists(button_path):
            location = pyautogui.locateOnScreen(button_path, confidence=confidence)
            if location:
                pyautogui.click(location)
                return True
        
        # If image not found, try OCR-based detection
        screen_text = get_screen_text()
        if button_text.lower() in screen_text.lower():
            # Get button coordinates using OCR
            data = pytesseract.image_to_data(pyautogui.screenshot(), output_type=pytesseract.Output.DICT)
            for i, text in enumerate(data['text']):
                if button_text.lower() in text.lower():
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    pyautogui.click(x + w//2, y + h//2)
                    return True
        
        return False
    except Exception as e:
        print(f"Error in button detection: {str(e)}")
        return False

def analyze_screen():
    """Analyze current screen and provide description with improved error handling"""
    try:
        screen_text = get_screen_text()
        if not screen_text:
            return "I couldn't detect any text on the screen."
        
        prompt = f"Based on the following screen text, provide a brief description of what's visible: {screen_text}"
        
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I can see text on the screen but couldn't analyze it: {screen_text[:100]}..."
            
    except Exception as e:
        return f"Error analyzing screen: {str(e)}"

def toggle_microphone():
    """Toggle microphone on/off with keyboard shortcut"""
    global mic_active
    mic_active = not mic_active
    if mic_active:
        print("\n[🎤 Microphone ON]")
        winsound.Beep(1000, 100)  # High pitch beep for ON
    else:
        print("\n[🎤 Microphone OFF]")
        winsound.Beep(500, 100)   # Low pitch beep for OFF

def microphone_thread():
    """Thread for continuous microphone listening"""
    global mic_active, stop_listening
    
    while not stop_listening:
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise... Please wait.")
                recognizer.adjust_for_ambient_noise(source, duration=2)
                print("Ambient noise adjustment complete.")
                
                while not stop_listening:
                    try:
                        print("\n[🎤 Listening...]")
                        play_listen()
                        
                        # Set dynamic energy threshold
                        recognizer.dynamic_energy_threshold = True
                        recognizer.energy_threshold = 4000
                        recognizer.pause_threshold = 0.8
                        recognizer.phrase_threshold = 0.3
                        recognizer.non_speaking_duration = 0.5
                        
                        try:
                            # Listen for speech with shorter timeout
                            audio = recognizer.listen(source, timeout=1, phrase_time_limit=None)
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as e:
                            if "listening timed out" not in str(e):
                                print(f"[❌ Listening error: {str(e)}]")
                            continue
                            
                        try:
                            query = recognizer.recognize_google(audio)
                            if query.strip():  # Only process non-empty queries
                                print(f"[👂 Heard]: {query}")
                                mic_queue.put(query.lower())
                        except sr.UnknownValueError:
                            pass
                        except sr.RequestError as e:
                            print(f"[❌ Could not request results; {e}]")
                            play_error()
                            speak("Sorry, there was an error with the speech recognition service.")
                    except Exception as e:
                        if "listening timed out" not in str(e):
                            print(f"[❌ Error in listening: {str(e)}]")
                        continue
        except Exception as e:
            print(f"[❌ Critical microphone error: {str(e)}]")
            print("Attempting to reinitialize microphone...")
            time.sleep(2)
            continue

def web_search(query, engine='google', max_results=5):
    """Perform web search and return results"""
    try:
        speak(f"Searching the web for {query}...")
        search_url = CONFIG['SEARCH_ENGINES'][engine] + query.replace(' ', '+')
        driver.get(search_url)
        
        # Wait for search results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.g" if engine == 'google' else "li.b_algo"))
        )
        
        # Extract search results
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
        else:
            elements = driver.find_elements(By.CSS_SELECTOR, "li.b_algo")[:max_results]
            for element in elements:
                try:
                    title = element.find_element(By.CSS_SELECTOR, "h2").text
                    link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    snippet = element.find_element(By.CSS_SELECTOR, "div.b_caption").text
                    results.append({"title": title, "link": link, "snippet": snippet})
                except:
                    continue
        
        return results
    except Exception as e:
        print(f"Error in web search: {str(e)}")
        return []

def get_llm_response(query, use_web_search=False):
    """Get response from LLM with optional web search"""
    try:
        context_text = ""
        
        if use_web_search:
            search_results = web_search(query)
            if search_results:
                context_text = "Based on the following search results:\n"
                for result in search_results:
                    context_text += f"Title: {result['title']}\nSnippet: {result['snippet']}\n\n"
        
        # Prepare the prompt
        prompt = f"""Context: {context_text}
        
        Question: {query}
        
        Please provide a comprehensive answer based on the context and your knowledge."""
        
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content":
"You are Sage, a dynamic and friendly voice assistant designed to assist with a wide range of tasks, from answering questions to performing actions, all through natural conversation. Your primary goal is to provide accurate, insightful, and context-aware responses, drawing on your broad knowledge and adaptability. Whether it's solving problems, offering creative ideas, or handling practical tasks, you engage users with a warm, conversational tone, making complex things simple and fun. As a voice-first companion, you listen carefully, respond thoughtfully, and aim to be the go-to helper for anything a user throws your way!"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in LLM response: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."

def process_query(query):
    """Process user queries"""
    global program_status, mic_active
    
    print(f"\n[🔍 Processing]: {query}")
    
    # Check for wake word
    if wakewords in query.lower():
        print("[✨ Assistant activated]")
        mic_active = True  # Activate the assistant
        speak("Yes boss? How can I help you?")
        return
    
    # Check if assistant was previously activated
    if not mic_active:
        print("[💤 Assistant is sleeping. Say 'sage' to activate]")
        return
        
    # Process commands
    try:
        if any(word in query for word in endwords):
            speak(f"Goodbye {user}!")
            mic_active = False  # Deactivate the assistant
            print("[👋 Assistant deactivated]")
            return

        elif "what's on my screen" in query or "describe my screen" in query:
            print("[🖥️ Analyzing screen...]")
            screen_description = analyze_screen()
            print_and_speak(screen_description)

        elif "click" in query and "button" in query:
            button_text = query.split("click")[-1].split("button")[-1].strip()
            print(f"[🖱️ Looking for button: {button_text}]")
            if find_and_click_button(button_text):
                print_and_speak(f"I've clicked the {button_text} button")
            else:
                print_and_speak(f"I couldn't find the {button_text} button")

        elif any(word in query for word in math_terms):
            expression = query.split("what is ")[-1]
            print(f"[🔢 Calculating: {expression}]")
            res = evaluate_math_expression(expression)                
            print_and_speak(f"The answer is : {res}")

        elif "open" in query:
            website = query.split("open ")[-1]
            print(f"[🌐 Opening website: {website}]")
            speak(f"opening {website}")
            webbrowser.open(f"https://www.{website}.com")
        
        elif 'news' in query:
            print("[📰 Fetching news...]")
            speak("Here are the latest news headlines:")
            news = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}&PageSize=5").json()
            for article in news['articles']:
                headline_list = article['title'].split("-")
                print_and_speak(headline_list[0:-1])
            speak(f"That is it for today's news {user}")

        elif 'the time' in query or 'current time' in query:
            time = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[🕒 Current time: {time}]")
            speak(f"The time is {time}")

        elif "weather in" in query:
            city = query.split("weather in ")[-1]
            print(f"[🌤️ Getting weather for: {city}]")
            weather_report = get_weather(city)
            print_and_speak(weather_report)

        elif "weather" in query:
            location = geocoder.ip('me')
            city = location.city
            print(f"[🌤️ Getting local weather for: {city}]")
            weather_report = get_weather(city)
            print_and_speak(weather_report)

        elif any(word in query for word in wiki):
            key = query.split(maxsplit=1)[-1]
            print(f"[📚 Searching Wikipedia for: {key}]")
            results = wikipedia.summary(key, sentences=1)
            print_and_speak(results)

        elif 'tell me a joke' in query:
            print("[😄 Fetching a joke...]")
            joke = requests.get("https://official-joke-api.appspot.com/random_joke").json()
            print_and_speak(joke['setup'])
            print_and_speak(joke['punchline'])

        elif 'how are you' in query:
            print("[💬 Casual conversation]")
            print_and_speak(f"I am fine, thank you for asking. How about you {user}?")

        elif 'fine' in query or 'good' in query:
            print("[💬 Casual conversation]")
            print_and_speak(f"That's great to hear{user}!")

        elif 'thank you' in query:
            print("[💬 Casual conversation]")
            print_and_speak(f"You're welcome {user}! If you have any more questions or need further assistance, feel free to ask.")

        elif 'search web for' in query or 'search the web for' in query:
            search_query = query.split('search web for')[-1].strip() if 'search web for' in query else query.split('search the web for')[-1].strip()
            print(f"[🔎 Searching web for: {search_query}]")
            response = get_llm_response(search_query, use_web_search=True)
            print_and_speak(response)

        else:
            # Use LLM without web search for general queries
            print("[🤖 Processing with AI...]")
            response = get_llm_response(query, use_web_search=False)
            print_and_speak(response)
            
    except Exception as e:
        print(f"[❌ Error processing command: {str(e)}]")
        speak("I'm sorry, I encountered an error while processing your request.")

def run_assistant():
    """Main function to run the voice assistant"""
    global program_status, mic_active
    
    try:
        x = ""
        hour = int(datetime.datetime.now().hour)
        if 0 <= hour < 12:
            x = f"Good Morning {user}!"
        elif 12 <= hour < 18:
            x = f"Good Afternoon {user}!"
        else:
            x = f"Good Evening {user}!"
        
        print("\n" + "="*50)
        print("🎙️  Voice Assistant (SAGE) 🤖")
        print("="*50)
        print("\nCommands:")
        print("- Press 'M' to toggle microphone")
        print("- Press 'Q' to quit")
        print("- Say 'sage' to activate")
        print("- Say 'search web for [query]' to search the web")
        print("- Say 'stop', 'end', or 'bye' to deactivate")
        print("="*50 + "\n")
        
        speak(f"{x} Call {wakewords} and I'll be at your service")
        
        # Start microphone thread
        mic_thread = threading.Thread(target=microphone_thread)
        mic_thread.daemon = True
        mic_thread.start()
        
        # Register keyboard shortcuts
        keyboard.on_press_key('m', lambda _: toggle_microphone())
        keyboard.on_press_key('q', lambda _: quit_assistant())
        
        # Main processing loop
        while program_status:
            try:
                if not mic_queue.empty():
                    query = mic_queue.get()
                    process_query(query)
                time.sleep(0.1)  # Prevent CPU overuse
            except Exception as e:
                print(f"[❌ Error in main loop: {str(e)}]")
                time.sleep(1)  # Wait before retrying
                continue
                
    except KeyboardInterrupt:
        print("\n[⚠️ Keyboard interrupt detected]")
        cleanup()
    except Exception as e:
        print(f"[❌ Critical error: {str(e)}]")
        cleanup()
    finally:
        cleanup()

def quit_assistant():
    """Handle graceful exit"""
    print("\n[👋 Quitting assistant...]")
    cleanup()
    os._exit(0)

def cleanup():
    """Cleanup resources before exit"""
    global stop_listening, program_status
    print("\n[🧹 Cleaning up resources...]")
    stop_listening = True
    program_status = False
    try:
        driver.quit()
    except:
        pass
    try:
        engine.stop()
    except:
        pass
    print("[✅ Cleanup complete]")

#Threads
intro_thread = threading.Thread(target=play_intro)
error_thread = threading.Thread(target=play_error)
intro_thread.start()

if __name__ == "__main__":
    try:
        # Initialize microphone as active
        mic_active = True
        run_assistant()
    except Exception as e:
        print(f"[❌ Fatal error: {str(e)}]")
        cleanup()
        os._exit(1)
 
 
 
