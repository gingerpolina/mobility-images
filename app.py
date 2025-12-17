import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
import random
import time
import os
import datetime

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v34 (Group Framing)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v34: Групповая Композиция")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК
# ==========================================

STYLE_PREFIX = "((NO REALISM)). 3D minimalist product render. Style: Matte plastic textures, smooth rounded shapes, soft studio lighting, ambient occlusion. Aesthetic: Playful, modern, high fidelity, C4D style, Octane render."
STYLE_SUFFIX = "High quality 3D render. 4k resolution."

# КОМПОЗИЦИЯ (ИСПРАВЛЕННАЯ: Группируем всё вместе)
COMPOSITION_RULES = (
    "VIEW: Wide Long shot. "
    "FRAMING LOGIC: Group the Main Object, the Rider, and the Environmental Elements together in the center of the image. "
    "MARGINS: Leave wide empty space between this entire group and the image borders. "
    "Ensure the Background Trees and Props are NOT cut off by the edges. "
    "Zoom out enough to fit the whole scene with padding."
)

# АНАТОМИЯ
SCOOTER_CORE = (
    "MAIN OBJECT: Modern Electric Kick Scooter. "
    "DESIGN RULES: 1. A tall vertical Blue tube (Steering stem) with T-handlebars. "
    "2. A wide, seamless, low-profile unibody standing deck (Snow White). "
    "3. Small minimalist wheels partially enclosed. "
    "SHAPE: Sleek, integrated, geometric L-shape. ((NO SEAT))."
)

CAR_CORE = "MAIN OBJECT: Cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."
COLOR_RULES = "COLORS: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."

# НЕГАТИВ
NEGATIVE_PROMPT = "realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, bench, box on deck, sitting, kneeling, riding sitting down, moped, motorcycle, cut off, cropped, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=45)
            if response.status_code == 200: return response.content
            elif response.status_code == 429:
                time.sleep(2 + attempt * 2)
                continue
        except:
            time.sleep(2 + attempt * 2)
            continue
    return None

def generate_image(prompt, width, height, seed, model='flux'):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=true&seed={seed}"
    return make_request_with_retry(url)

def smart_resize(image_bytes, target_w, target_h):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.size[0] < target_w or img.size[1] < target_h:
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        buf = io.BytesIO(); img.save(buf, format="PNG")
        return buf.getvalue()
    except: return image_bytes

def translate_text(text):
    if not text or not HAS_TRANSLATOR: return text
    try: return GoogleTranslator(source='auto', target='en').translate(text)
    except: return text

#
