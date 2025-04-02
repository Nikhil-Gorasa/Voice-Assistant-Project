from PIL import Image, ImageDraw

def create_icon():
    # Create a 256x256 image with a transparent background
    size = 256
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a circle
    margin = 20
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(52, 152, 219, 255))  # Blue circle
    
    # Draw a microphone symbol
    mic_width = 80
    mic_height = 120
    x = (size - mic_width) // 2
    y = (size - mic_height) // 2
    
    # Draw the microphone body
    draw.rectangle([x+20, y+20, x+60, y+100], fill=(255, 255, 255, 255))
    # Draw the microphone stand
    draw.rectangle([x+35, y+100, x+65, y+120], fill=(255, 255, 255, 255))
    
    # Save the icon
    image.save('icon.png')

if __name__ == "__main__":
    create_icon() 