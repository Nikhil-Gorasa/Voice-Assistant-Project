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
from playsound import playsound
import pyautogui
import cv2
import numpy as np
import pytesseract
from together import Together
import pathlib

# Configuration
CONFIG = {
    'SOUND_FILES': {
        'intro': 'sounds/intro.mp3',
        'listen': 'sounds/error-2.mp3',
        'error': 'sounds/short-beep-tone.mp3'
    },
    'TESSERACT_CMD': r'C:\Program Files\Tesseract-OCR\tesseract.exe',  # Windows default path
    'BUTTON_IMAGES_DIR': 'button_images',
    'SCREENSHOT_DIR': 'screenshots'
}

# Create necessary directories
for dir_path in [CONFIG['BUTTON_IMAGES_DIR'], CONFIG['SCREENSHOT_DIR']]:
    pathlib.Path(dir_path).mkdir(exist_ok=True)

# Initialize Together API client
dotenv.load_dotenv()
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', "f15ba22ed0665375913552d87afef7ddef0ba28cfe2ff8976d6ce81e92ad4450")
client = Together(api_key=TOGETHER_API_KEY)

# Initialize Tesseract
pytesseract.pytesseract.tesseract_cmd = CONFIG['TESSERACT_CMD']

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
        sound_path = CONFIG['SOUND_FILES'].get(sound_type)
        if sound_path and os.path.exists(sound_path):
            playsound(sound_path)
        else:
            print(f"Sound file not found: {sound_path}")
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
			speak(f"Apologies, could you please repeat that  {user}?")
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

def get_llm_response(query, max_retries=3):
    """Get response from LLM for general queries with retry mechanism"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": query}],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == max_retries - 1:
                return f"I apologize, but I'm having trouble processing your request right now. Please try again later."
            print(f"LLM API error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            continue

def process_query(query):
    print(query)
    global program_status

    if wakewords in query:
        speak("Yes boss? How can i help you ?")
        while True:
            query = listen()
            if any(word in query for word in endwords):
                speak(f"Goodbye {user}!")
                program_status = False
                print("Program Stopped! Assistant is inactive")
                break

            elif "what's on my screen" in query or "describe my screen" in query:
                screen_description = analyze_screen()
                print_and_speak(screen_description)

            elif "click" in query and "button" in query:
                button_text = query.split("click")[-1].split("button")[-1].strip()
                if find_and_click_button(button_text):
                    print_and_speak(f"I've clicked the {button_text} button")
                else:
                    print_and_speak(f"I couldn't find the {button_text} button")

            elif any(word in query for word in math_terms):
                expression = query.split("what is ")[-1]
                res = evaluate_math_expression(expression)                
                print_and_speak(f"The answer is : {res}")
    
            elif "open" in query:
                website = query.split("open ")[-1]
                speak(f"opening {website}")
                webbrowser.open(f"https://www.{website}.com")
            
            elif 'news' in query:
                speak("Here are the latest news headlines:")
                news = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}&PageSize=5").json()
                for article in news['articles']:
                    headline_list = article['title'].split("-")
                    print_and_speak(headline_list[0:-1])
                speak(f"That is it for today's news {user}")
    
            elif 'the time' in query or 'current time' in query:
                time = datetime.datetime.now().strftime("%H:%M:%S")
                speak(f"The time is {time}")
    
            elif "weather in" in query:
                city = query.split("weather in ")[-1]
                weather_report = get_weather(city)
                print_and_speak(weather_report)
    
            elif "weather" in query:
                location = geocoder.ip('me')
                city=location.city
                weather_report = get_weather(city)
                print_and_speak(weather_report)
    
            elif any(word in query for word in wiki):
                key = query.split(maxsplit=1)[-1]
                results = wikipedia.summary(key, sentences=1)
                print_and_speak(results)
    
            elif 'tell me a joke' in query:
                joke = requests.get("https://official-joke-api.appspot.com/random_joke").json()
                print_and_speak(joke['setup'])
                print_and_speak(joke['punchline'])
    
            elif 'how are you' in query:
                print_and_speak(f"I am fine, thank you for asking. How about you {user}?")
    
            elif 'fine' in query or 'good' in query:
                print_and_speak(f"That's great to hear{user}!")
    
            elif 'thank you' in query:
                print_and_speak(f"You're welcome {user}! If you have any more questions or need further assistance, feel free to ask. ")
	   
            else:
                # Use LLM for general queries
                response = get_llm_response(query)
                print_and_speak(response)
    else:
        print("Say the wakeword ! ")

def run_assistant():
	x=""
	hour = int(datetime.datetime.now().hour)
	if 0 <= hour < 12:
		x = f"Good Morning{user}!"
	elif 12 <= hour < 18:
		x = f"Good Afternoon{user}!"
	else:
		x = f"Good Evening{user}!"
	speak(f"{x}  Call {wakewords} and i'll be at your service")
	while program_status:
		process_query(listen())
	engine.endLoop()

#Threads
intro_thread = threading.Thread(target=play_intro)
error_thread = threading.Thread(target=play_error)
intro_thread.start()

if __name__ == '__main__':
	program_status = True
	print("Assistant is Active")
	print("Please tell the WakeWords")
	run_assistant()
 
 
 
