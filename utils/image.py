from io import BytesIO

from PIL import Image, ImageDraw, ImageFont



# Load a high-quality TrueType font
def load_font(font_path, size):
    return ImageFont.truetype(font_path, size)


# Create the image with a background image
def create_image(symbol, price, market_cap, liquidity, change, background_path):
    # Load the background image
    img = Image.open(background_path)

    draw = ImageDraw.Draw(img)

    # Load high-quality font
    title_font = load_font('Roboto-Bold.ttf', 30)  # Large title font
    body_font = load_font('Roboto-Regular.ttf', 30)  # Body font

    change_number = float(change[:-1])
    change_color = (4, 133, 71) if change_number >= 0 else (205, 0, 0)

    draw.text((280, 50), symbol.upper(), font=title_font, fill=(255, 255, 255))

    # Add other details with appropriate spacing and sizes
    draw.text((130, 165), price, font=body_font, fill=(255, 255, 255))
    draw.text((135, 275), market_cap, font=body_font, fill=(255, 255, 255))
    draw.text((390, 275), liquidity, font=body_font, fill=(255, 255, 255))
    draw.text((395, 165), change, font=body_font, fill=change_color)

    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)  # Move the cursor to the beginning of the BytesIO object

    return img_buffer


