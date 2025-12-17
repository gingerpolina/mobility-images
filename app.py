import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
import random
import time
import os
import datetime

# --- CONFIG ---
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR): os.makedirs(GALLERY_DIR)
# Нейтральное название
st.set_page_config(page_title="Scooter Gen v41", layout="wide", page_icon="🛴")
st.title("🛴 Scooter Gen v41: Пропорции и Поза")

if 'last_image_bytes' not in st.session_state: st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state: st.session_state.last_image_size = (0, 0)

# Try import translator safely
try: from deep_translator import GoogleTranslator; HAS_TRANSLATOR = True
except ImportError: HAS_TRANSLATOR = False

# --- PROMPT CONSTANTS (BASE v39) ---
STYLE_PREFIX = "((NO REALISM)). 3D minimalist product render. Style: Matte plastic textures, smooth rounded shapes, soft studio lighting, ambient occlusion. Aesthetic: Playful, modern, high fidelity, C4D style, Octane render."
STYLE_SUFFIX = "High quality 3D render. 4k resolution."

# GROUP FRAMING
COMPOSITION_RULES = "VIEW: Long shot (Full Body). COMPOSITION: The Main Object, the Rider, and the Environmental Props are GROUPED together in the center. MARGINS: Leave 20% empty background padding around this ENTIRE GROUP. Ensure trees and props are NOT cut off. Zoom out."

# UNIBODY ANATOMY
SCOOTER_CORE = "MAIN OBJECT: Modern Electric Kick Scooter. DESIGN: 1. Tall vertical Blue tube (Steering stem) with T-handlebars. 2. Wide, seamless, low-profile unibody standing deck (Snow White). 3. Small minimalist wheels partially enclosed. SHAPE: Sleek, integrated, geometric L-shape. ((NO SEAT))."
CAR_CORE = "MAIN OBJECT: Cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."
COLOR_RULES = "COLORS: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."
NEGATIVE_PROMPT = "realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, bench, sitting, kneeling, four legs, crawling, moped, motorcycle, cut off, cropped, text, watermark, levitation, hovering feet, jumping, tiny character"

# --- FUNCTIONS ---
def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=45)
            if response.status_code == 200: return response.content
            elif response.status_code == 429: time.sleep(2 + attempt * 2); continue
        except: time.sleep(2 + attempt * 2); continue
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

# --- UI LOGIC ---
tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.form("gen_form"):
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            passenger_input = st.text_input("👤 Пассажир:", placeholder="Например: Кот...")
            st.divider()
            # Нейтральные названия цветов
            color_theme = st.selectbox("🎨 Окружение:", ["🟦 Royal Blue", "⬜ Flat White", "🟧 Neon Orange", "🎨 Natural", "⬛ Matte Black"])
            env_input = st.text_area("🌳 Детали окружения:", height=80)
            aspect = st.selectbox("Формат:", ["1:1", "16:9", "9:16"])
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            env_en = translate_text(env_input) if env_input else ""
            pass_en = translate_text(passenger_input) if passenger_input else ""

            # --- ИСПРАВЛЕННАЯ ЛОГИКА (V41 - TOY BODY + SCALE + STANCE) ---
            if pass_en:
                if "Самокат" in mode:
                    passenger_prompt = (
                        "RIDER: A cute 3D plastic toy character of " + pass_en + ". " +
                        # 1. ТЕЛО (ИЗ V39)
                        "BODY
