import pyttsx3
import speech_recognition as sr
import together
import os
import dotenv
import pyautogui
import pytesseract
import cv2
import numpy as np
from PIL import Image
import datetime

# Load environment variables
dotenv.load_dotenv()
together.api_key = os.getenv('TOGETHER_API_KEY')

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 180)

# Initialize speech recognition
recognizer = sr.Recognizer()

def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        print("Processing...")
        try:
            query = recognizer.recognize_google(audio)
            print(f"You said: {query}")
            return query.lower()
        except Exception as e:
            print(f"Error: {str(e)}")
            return ""

def get_screen_text():
    try:
        # Take screenshot
        print("Capturing screenshot...")
        screenshot = pyautogui.screenshot()
        
        # Save screenshot for debugging
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join("screenshots", f"screenshot_{timestamp}.png")
        screenshot.save(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Convert to OpenCV format
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to preprocess the image
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Save preprocessed image for debugging
        cv2.imwrite(os.path.join("screenshots", f"preprocessed_{timestamp}.png"), thresh)
        
        # Apply OCR with different configurations
        text = pytesseract.image_to_string(thresh, config='--psm 6')
        if not text.strip():
            print("First OCR attempt failed, trying different configuration...")
            text = pytesseract.image_to_string(thresh, config='--psm 3')
        
        if text.strip():
            print("OCR successful")
            return text.strip()
        else:
            print("OCR failed to detect any text")
            return ""
    except Exception as e:
        print(f"Screen capture error: {str(e)}")
        return ""

def find_and_click_button(button_text):
    try:
        print(f"Looking for button with text: {button_text}")
        # Get screen text and coordinates
        screenshot = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Save screenshot for debugging
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(os.path.join("screenshots", f"button_search_{timestamp}.png"), img)
        
        # Try OCR with different configurations
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config='--psm 6')
        
        # Search for button text
        found = False
        for i, text in enumerate(data['text']):
            if button_text.lower() in text.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = int(data['conf'][i])
                
                print(f"Found potential match: '{text}' at ({x}, {y}) with confidence {conf}%")
                
                if conf > 60:  # Only click if confidence is high enough
                    # Click center of text
                    center_x = x + w//2
                    center_y = y + h//2
                    print(f"Clicking at coordinates: ({center_x}, {center_y})")
                    pyautogui.click(center_x, center_y)
                    found = True
                    break
        
        if not found:
            print("Button text not found with high confidence")
            return False
        return True
    except Exception as e:
        print(f"Button click error: {str(e)}")
        return False

def get_llm_response(query, screen_context=None):
    try:
        # Include screen context if available
        if screen_context:
            prompt = (
                f"Human: The current screen shows the following text:\n\n"
                f"{screen_context}\n\n"
                f"Based on this screen content, please {query}\n"
                f"Assistant:"
            )
        else:
            prompt = f"Human: {query}\nAssistant:"
        
        print(f"\nSending prompt to LLM:\n{prompt}\n")
            
        output = together.Complete.create(
            prompt=prompt,
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            max_tokens=200,
            temperature=0.7,
            stop=['Human:', '\n\n']
        )
        
        print(f"\nRaw LLM response: {output}\n")
        
        if isinstance(output, dict):
            if 'choices' in output:
                return output['choices'][0]['text'].strip()
            elif 'output' in output and 'choices' in output['output']:
                return output['output']['choices'][0]['text'].strip()
            else:
                print(f"Unexpected API response structure: {output.keys()}")
                return "I'm having trouble understanding the screen content. Could you please try again?"
        else:
            print(f"Unexpected API response type: {type(output)}")
            return "I'm having trouble processing the information. Could you please try again?"
    except Exception as e:
        print(f"API Error: {str(e)}")
        return "I'm having trouble connecting to my language model. Please try again in a moment."

def main():
    print("Voice Assistant Test Mode")
    print("Say 'exit' to quit")
    print("\nAvailable commands:")
    print("- 'What's on my screen?' - Get a description of the current screen")
    print("- 'Click [button name] button' - Click a button on the screen")
    print("- 'Exit' - End the program")
    print("\nListening for commands...")
    
    while True:
        query = listen()
        if query:
            if "exit" in query:
                speak("Goodbye!")
                break
            elif "what's on my screen" in query or "what is on my screen" in query:
                screen_text = get_screen_text()
                if screen_text:
                    response = get_llm_response("provide a clear and concise description of what is shown on the screen", screen_text)
                    speak(response)
                else:
                    speak("I'm having trouble reading the screen right now. Please make sure the screen content is clear and visible.")
            elif "click" in query and "button" in query:
                button_text = query.split("click")[-1].split("button")[0].strip()
                if find_and_click_button(button_text):
                    speak(f"I've clicked the {button_text} button")
                else:
                    speak(f"I couldn't find a button labeled '{button_text}'. Please make sure the button is visible on the screen.")
            else:
                # Get screen context for relevant queries
                screen_text = None
                if any(word in query for word in ["screen", "see", "show", "display"]):
                    screen_text = get_screen_text()
                response = get_llm_response(query, screen_text)
                speak(response)

if __name__ == "__main__":
    main() 