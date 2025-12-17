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
# 1. НАСТРОЙКИ И ПАПКИ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v17.2 (Stable Blue)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v17.2: Синий Студийный")

# Инициализация памяти (чтобы картинка не исчезала)
if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (Стиль и Промпты)
# ==========================================

# Стиль
STYLE_PREFIX = (
    "((NO REALISM)). ((3D Claymorphism Render)), ((Matte Soft Plastic Material)). "
    "LOOK: Cute, Minimalist, Smooth rounded edges, Toy-like proportions. "
    "LIGHTING: Bright Softbox lighting, clean shadows. "
)

STYLE_SUFFIX = "Everything is made of matte plastic. Unreal Engine 5. Blender 3D."

# Анатомия (Анти-сиденье)
SCOOTER_CORE = (
    "OBJECT: A modern Stand-up Electric Kickboard. "
    "ANATOMY: A flat skateboard-like deck (Snow White) + A vertical T-bar handle (Royal Blue). "
    "((STRICTLY NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). "
    "The object is designed for STANDING only. "
)

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Details (#FF9601). NO PINK."

NEGATIVE_PROMPT = "(seat:3.0), (saddle:3.0), (chair:3.0), moped, vespa, motorcycle, realistic, photo, metal, chrome, reflection, dirt, grunge, pink, purple, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        # Тайм-аут: 80 сек для больших, 30 для маленьких
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

# ==========================================
# 4. ИНТЕРФЕЙС
# ==========================================

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# --- ВКЛАДКА 1: ГЕНЕРАТОР ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            # ВЫБОР ФОНА (Добавили Синий)
            bg_select = st.selectbox("Фон:", [
                "⬜ Студийный Белый", 
                "🟦 Студийный Синий (Бренд)",
                "🏙️ Улица (Размытая)", 
                "🌳 Парк (Зелень)", 
                "🌃 Ночной Город (Неон)"
            ])
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Детали (например: стоит у столба):", height=80)
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        # ЛОГИКА ГЕНЕРАЦИИ
        if submitted and user_input:
            # 1. Перевод
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input)
            except:
                scene_en = user_input
            
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            # 2. Настройка Фона (Вот здесь исправлены отступы!)
            if "Белый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid White Hex #FFFFFF)). Isolated."
            elif "Синий" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Royal Blue Hex #0668D7)). Minimalist studio backdrop. No shadows."
            elif "Улица" in bg_select:
                bg_prompt = "BACKGROUND: Blurred minimalist city street, bokeh, plastic style buildings."
            elif "Парк" in bg_select:
                bg_prompt = "BACKGROUND: Minimalist plastic park, abstract green trees, soft sunlight."
            elif "Ночной" in bg_select:
                bg_prompt = "BACKGROUND: Dark blue night city, soft neon lights, bokeh, plastic style."
            else:
                bg_prompt = "BACKGROUND: ((Solid White Hex #FFFFFF))."

            # 3. Сборка Промпта
            if "Самокат" in mode:
                scene_context = f"SCENE: {clean_scene}. The object looks like a skateboard with a handle."
                raw_prompt = f"{STYLE_PREFIX} {SCOOTER_CORE} {scene_context} {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} SCENE: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 4. Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 5. Запрос к серверу
            with st.spinner("Генерация..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят (429). Подождите 5 секунд.")
            elif img_bytes:
                # Сохраняем в память се
