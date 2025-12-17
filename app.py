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

st.set_page_config(page_title="Urent Gen v25 (Pro)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v25: Пассажиры и Композиция")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (ОБНОВЛЕННЫЙ)
# ==========================================

# СТИЛЬ: Тот самый, из твоего запроса + защита от фотореализма
STYLE_PREFIX = (
    "((NO REALISM)). ((3D minimalist illustration)), ((matte plastic textures)), ((3D claymorphism)). "
    "LOOK: Smooth rounded shapes, soft studio lighting, ambient occlusion, clean solid background. "
    "RENDER: Octane render, high fidelity, playful and modern aesthetic, C4D style. "
    "VIBE: Floating rounded objects, abstract joyful atmosphere. "
)

STYLE_SUFFIX = "High quality 3D render. 4k."

# КОМПОЗИЦИЯ: Защита от обрезания (Zoom Out)
COMPOSITION_RULES = (
    "((Whole object strictly inside frame)). ((Wide margins)). ((Zoom out)). "
    "((Plenty of negative space around the object)). "
    "Nothing is cut off by the borders. Centered composition."
)

# АНАТОМИЯ:
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
            st.subheader("🛠️ Конструктор Сцены")
            
            # 1. Объект
            mode = st.radio("Транспорт:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            # 2. Пассажир (Новое!)
            passenger_input = st.text_input("👤 Пассажир (Оставь пустым, если никого):", placeholder="Например: Дед Мороз, Кот в очках...")
            
            st.divider()
            
            # 3. Атмосфера и Цвета (Новое!)
            color_theme = st.selectbox("🎨 Цветовая гамма окружения:", [
                "🟦 Urent Blue (Синий монохром)", 
                "⬜ Flat White (Белый минимализм)", 
                "🟧 Urent Orange (Оранжевый взрыв)",
                "🎨 Natural (Естественные цвета)",
                "⬛ Matte Black (Черный стиль)"
            ])
            
            # 4. Окружение
            env_input = st.text_area("🌳 Окружение (Что вокруг?):", height=80, placeholder="Например: елки, подарочные коробки, уличные фонари...")
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # === ЭТАП 1: ОБРАБОТКА ТЕКСТА ===
            translator = GoogleTranslator(source='auto', target='en')
            
            # Перевод окружения
            if env_input:
                try: env_en = translator.translate(env_input)
                except: env_en = env_input
            else:
                env_en = "minimalist abstract shapes, floating rounded elements" # Дефолтный фон, если пусто

            # Перевод пассажира
            if passenger_input:
                try: pass_en = translator.translate(passenger_input)
                except: pass_en = passenger_input
                # Делаем пассажира игрушечным
                passenger_prompt = f"RIDER: A cute 3D plastic toy character of {pass_en} is standing on the deck holding the handle."
            else:
                passenger_prompt = "No rider, empty vehicle. ((NO SEAT))."

            # === ЭТАП 2: ЛОГИКА ЦВЕТА (MONOCHROME MAGIC) ===
            # Мы красим объекты окружения в цвет фона, чтобы получить стиль
            
            if "Blue" in color_theme:
                bg_prompt = "BACKGROUND: Solid Royal Blue Hex #0668D7. No shadows."
                env_style = f"ENVIRONMENT: {env_en}. All environment elements are made of Matte Royal Blue Plastic to match the background."
            elif "Orange" in color_theme:
                bg_prompt = "BACKGROUND: Solid Neon Orange Hex #FF9601. No shadows."
                env_style = f"ENVIRONMENT: {env_en}. All environment elements are made of Matte Orange Plastic."
            elif "White" in color_theme:
                bg_prompt = "BACKGROUND: Solid Flat White. No shadows."
                env_style = f"ENVIRONMENT: {env_en}. All environment elements are made of Matte White Plastic."
            elif "Black" in color_theme:
                bg_prompt = "BACKGROUND: Solid Matte Black. No shadows."
                env_style = f"ENVIRONMENT: {env_en}. All environment elements are Dark Grey or Black Plastic."
            else: # Natural
                bg_prompt = "BACKGROUND: Clean Studio Lighting. Soft gradient."
                env_style = f"ENVIRONMENT: {env_en}. Elements have colorful matte plastic toy look."

            # === ЭТАП 3: СБОРКА ПРОМПТА ===
            
            if "Самокат" in mode:
                core = SCOOTER_CORE
            elif "Машина" in mode:
                core = CAR_CORE
            else:
                core = f"MAIN OBJECT: {env_en}" # Если выбрано "Другое"
            
            # Финальная формула
            raw_prompt = (
                f"{STYLE_PREFIX} {COMPOSITION_RULES} "
                f"{core} {passenger_prompt} "
                f"{env_style} {COLOR_RULES} {bg_prompt} "
                f"{STYLE_SUFFIX}"
            )
            
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # === ЭТАП 4: ГЕНЕРАЦИЯ ===
            with st.spinner("Рендер сцены..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят (4
