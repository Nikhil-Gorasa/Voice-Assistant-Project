# Voice Assistant (SAGE)

A powerful voice assistant with screen understanding and LLM capabilities.

## Features

- Voice recognition and text-to-speech
- Screen text recognition and analysis
- Button detection and clicking
- LLM-powered responses
- Weather information
- News updates
- Wikipedia queries
- Mathematical calculations
- Web browsing
- Jokes and general conversation

## Prerequisites

1. Python 3.8 or higher
2. Tesseract OCR installed on your system
   - Windows: Download and install from [Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - Mac: `brew install tesseract`

## Installation

1. Clone the repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your API keys:
   ```
   NEWS_API_KEY=your_news_api_key
   OPENWEATHERMAP_API_KEY=your_weather_api_key
   TOGETHER_API_KEY=your_together_api_key
   ```
4. Create required directories:
   - `sounds/` - Place your sound files here
   - `button_images/` - Place button images here
   - `screenshots/` - For debugging screenshots

## Sound Files

Place the following sound files in the `sounds/` directory:
- `intro.mp3` - Introduction sound
- `error-2.mp3` - Listening sound
- `short-beep-tone.mp3` - Error sound

## Button Images

For button clicking functionality, save button images in the `button_images/` directory with the format:
`button_[button_name].png`

## Usage

1. Run the assistant:
   ```bash
   python voice_assistant.py
   ```
2. Say the wake word "sage" to activate the assistant
3. Available commands:
   - "What's on my screen?" - Get screen description
   - "Click [button name] button" - Click a button
   - "Open [website]" - Open a website
   - "Weather in [city]" - Get weather information
   - "Tell me a joke" - Get a random joke
   - "What is [query]" - Wikipedia search
   - "News" - Get latest news
   - Any other query will be processed by the LLM

## Troubleshooting

1. If Tesseract OCR fails:
   - Verify Tesseract is installed correctly
   - Check the path in CONFIG['TESSERACT_CMD']

2. If sound files don't play:
   - Verify sound files exist in the `sounds/` directory
   - Check file permissions

3. If button clicking fails:
   - Verify button images exist in `button_images/`
   - Check image quality and resolution

4. If LLM responses fail:
   - Verify API key in `.env`
   - Check internet connection
   - Verify API rate limits

## Contributing

Feel free to submit issues and enhancement requests!
