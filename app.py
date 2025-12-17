import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time
import os
import datetime
import shutil

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v26 (Platinum)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v26: Platinum Stable")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (ОБНОВЛЕННЫЙ)
# ==========================================

# СТИЛЬ: Твой оригинальный запрос + защита от реализма
STYLE_PREFIX = (
    "((NO REALISM)). style of 3D minimalist illustration, matte plastic textures, "
    "smooth rounded shapes, soft studio lighting, ambient occlusion, vibrant colors, "
    "clean solid background, Octane render, high fidelity, 3D claymorphism, "
    "playful and modern aesthetic, C4D style. "
)

STYLE_SUFFIX = "High quality 3D render. 4k."

# КОМПОЗИЦИЯ: Чтобы не обрезалось
COMPOSITION_RULES = (
    "((Whole object strictly inside frame)). ((Wide margins)). ((Zoom out)). "
    "((Plenty of negative space around the object)). "
    "Nothing is cut off by the borders. Centered composition. "
)

# АНАТОМИЯ
SCOOTER_CORE = (
    "MAIN OBJECT: A cute thick Electric Kickboard. "
    "DESIGN: Thick vertical blue tube stem, wide flat white deck, minimalist enclosed wheels. "
    "SHAPE: Geometric, sturdy, robust. "
)

CAR_CORE = "MAIN OBJECT: A cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."

# ЦВЕТА
COLOR_RULES = "COLORS: Matte Snow White Body (#EAF0F9), Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."

NEGATIVE_PROMPT = "realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, cut off, cropped, out of frame, close up, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        timeout_val = 80 if width > 1200 else 30
        response = requests.get(url, timeout=timeout_val)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

def smart_resize(image_bytes, target_w, target_h):
    img = Image.open(io.BytesIO(image_bytes))
    current_w, current_h = img.size
    if current_w < target_w or current_h < target_h:
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==========================================
# 4. ИНТЕРФЕЙС
# ==========================================

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("🛠️ Конструктор")
            
            # 1. Объект
            mode = st.radio("Транспорт:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            # 2. Пассажир
            passenger_input = st.text_input("👤 Пассажир (Пусто = без никого):", placeholder="Например: Дед Мороз, Кот...")
            
            st.divider()
            
            # 3. Цветовая гамма окружения
            color_theme = st.selectbox("🎨 Палитра окружения/фона:", [
                "🟦 Urent Blue (Синий монохром)", 
                "⬜ Flat White (Белый минимализм)", 
                "🟧 Urent Orange (Оранжевый взрыв)",
                "🎨 Natural (Естественные цвета)",
                "⬛ Matte Black (Черный стиль)"
            ])
            
            # 4. Окружение
            env_input = st.text_area("🌳 Детали окружения (Пусто = студийный фон):", height=80, placeholder="Например: елки, коробки...")
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # === 1. ПЕРЕВОД ===
            translator = GoogleTranslator(source
