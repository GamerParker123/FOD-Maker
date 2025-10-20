import requests
from PIL import Image, ImageDraw, ImageFont
import datetime
import random
import os

# === Settings ===
FONT_PATH = "Anton-Regular.ttf"  # Replace with the path to your desired .ttf font
IMAGE_FOLDER = "fod_images"  # Folder with transparent PNGs
OUTPUT_FOLDER = "output"  # Where to save the slides
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Step 1: Get a Random Fact ===
def get_random_fact():
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["text"].replace("`", "'")
    except Exception as e:
        print("Error fetching fact:", e)
        return "Fun Fact: Whales are cool."

# === Step 2: Word wrap function ===
def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if font.getlength(test_line) <= max_width:
            line = test_line
        else:
            lines.append(line.strip())
            line = word + " "
    lines.append(line.strip())
    return lines

# === Step 3: Generate the Slide ===
def generate_slide(fact_text):
    today = datetime.date.today()
    date_str = f"{today.month}/{today.day}/{today.year % 100}"
    W, H = 960, 540
    image_on_left = datetime.date.today().day % 2 == 1
    def get_dark_color():
        while True:
            color = tuple(random.randint(0, 255) for _ in range(3))
            # Use luminance formula: 0.299*R + 0.587*G + 0.114*B
            brightness = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
            if brightness < 160:  # tweak threshold as needed
                return color

    bg_color = get_dark_color()

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Auto-scale title font to fit width (max 400px)
    title_text = f"FOD {date_str}:"
    max_title_width = 400
    max_title_font_size = 48
    min_title_font_size = 16
    title_font_size = max_title_font_size

    while title_font_size >= min_title_font_size:
        title_font = ImageFont.truetype(FONT_PATH, title_font_size)
        text_width = title_font.getlength(title_text)
        if text_width <= max_title_width:
            break
        title_font_size -= 2

    # load font
    fact_font = ImageFont.truetype(FONT_PATH, 36)

    # Load random image
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(".png")]
    if not images:
        raise Exception("No images found in folder.")
    img_path = os.path.join(IMAGE_FOLDER, random.choice(images))
    fg_img = Image.open(img_path).convert("RGBA")
    fg_img.thumbnail((400, 400))
    img_x = 50 if image_on_left else W - fg_img.width - 50
    img_y = (H - fg_img.height) // 2
    img.paste(fg_img, (img_x, img_y), fg_img)
    text_x = W - fg_img.width - 50 if image_on_left else 50

    # === Auto-scale fact with reroll and pre-check ===
    max_fact_height = int(H * 0.6)
    max_font_size = 48
    min_font_size = 16
    max_words = 40
    reroll_limit = 10
    rerolls = 0

    while rerolls < reroll_limit:
        # Pre-check word count
        word_count = len(fact_text.split())
        if word_count > max_words:
            print(f"↻ Fact too long ({word_count} words), rerolling...")
            fact_text = get_random_fact()
            rerolls += 1
            continue

       # Now try to auto-scale the font
        font_size = max_font_size
        while font_size >= min_font_size:
            fact_font = ImageFont.truetype(FONT_PATH, font_size)
            lines = wrap_text(fact_text, fact_font, 400, draw)
            bbox = fact_font.getbbox("A")
            line_height = bbox[3] - bbox[1] + 5
            total_text_height = len(lines) * line_height

            if total_text_height <= max_fact_height:
                break  # ✅ fits
            font_size -= 2

        if total_text_height <= max_fact_height:
            break  # ✅ Fact is good and fits
        else:
            print("↻ Fact still doesn't fit after scaling, rerolling...")
            fact_text = get_random_fact()
            rerolls += 1

    if rerolls == reroll_limit:
        print("⚠️ Could not find a short-enough fact after multiple attempts.")
        fact_text = "Fun Fact: Whales are cool."
        fact_font = ImageFont.truetype(FONT_PATH, 36)
        lines = wrap_text(fact_text, fact_font, 400, draw)
        bbox = fact_font.getbbox("A")
        line_height = bbox[3] - bbox[1] + 5
        total_text_height = len(lines) * line_height


    # Center vertically
    start_y = (H - total_text_height) // 2

    # Draw text
    y = start_y
    for line in lines:
        draw.text((text_x, y), line, font=fact_font, fill="white")
        y += line_height
    draw.text((text_x, 50), title_text, font=title_font, fill="white") # draw title
    # Measure title size
    title_bbox = title_font.getbbox(title_text)
    title_height = title_bbox[3] - title_bbox[1]
    title_width = title_font.getlength(title_text)

    # Underline position
    underline_y = 50 + title_height + 18  # 18px below the text baseline
    draw.line(
        [(text_x, underline_y), (text_x + title_width, underline_y)],
        fill="white",
        width=4  # Adjust thickness here
    )

    # Save the slide
    filename = f"FOD{today.strftime("%m%d%y").replace("-", "")}.png"
    full_path = os.path.join(OUTPUT_FOLDER, filename)
    img.save(full_path)
    print(f"✅ Slide saved: {full_path}")
    return full_path, date_str

# === Step 4: Run Everything ===
if __name__ == "__main__":
    fact = get_random_fact()
    slide_path, date_str = generate_slide(fact)
    print(f"FOD {date_str}: {fact}")