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

engine = pyttsx3.init()
engine.setProperty('rate', 180)
recognizer = sr.Recognizer()

#API keys
dotenv.load_dotenv()
NEWS_API_KEY=os.getenv('NEWS_API_KEY')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_APT_KEY')

# Words
endwords = ["stop", "end", "bye"]
wakewords = "sage"
wiki = ["what is ","what are ","who is ","who are "]
math_terms= ["plus","minus","divided by","into","multiplied by","by","+","-","*","/","x"]
user = "boss"

def play_intro():
	playsound("D:\CODE\PYTHON\project\Voice Assistant Project\intro.mp3")

def play_listen():
	playsound("D:\CODE\PYTHON\project\Voice Assistant Project\error-2.mp3")

def play_error():
    playsound("D:\CODE\PYTHON\project\Voice Assistant Project\short-beep-tone.mp3")
   
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
				print_and_speak(f"I am not capable of processing this request yet !.Sorry {user}")
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