import wave
import struct
import os

def generate_sound(filename, duration=0.1, frequency=440, volume=0.5):
    # Audio parameters
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    
    # Create WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Generate samples
        for i in range(num_samples):
            value = int(volume * 32767 * (1 - i/num_samples))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)

def main():
    # Create sounds directory if it doesn't exist
    if not os.path.exists('sounds'):
        os.makedirs('sounds')
    
    # Generate test sound files
    generate_sound('sounds/intro.mp3', duration=0.5)
    generate_sound('sounds/error-2.mp3', duration=0.3)
    generate_sound('sounds/short-beep-tone.mp3', duration=0.2)
    
    print("Test sound files generated successfully!")

if __name__ == "__main__":
    main() 