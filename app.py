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

# --- ПАПКА ДЛЯ КАРТИНОК ---
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

# --- БРЕНДБУК ---
STYLE_PREFIX = """
((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)).
LOOK: Minimalist, Clean geometry, Toy-like but premium.
LIGHTING: Studio softbox, global illumination, no harsh shadows.
"""
STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

OBJECT_CORE = """
OBJECT: A modern Electric Kickboard (Stand-up vehicle).
FORM: Thick vertical tube (Royal Blue), wide flat deck (Snow White).
((NO SEAT)), ((NO SADDLE)). Standing only.
"""
CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Wires (#FF9601). NO PINK."
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)). No walls, no floor texture."
NEGATIVE_PROMPT = "photo, realistic, metal, chrome, seat, saddle, motorcycle, scooter, pink, purple, complex background, text, watermark"

# -----------------------------------------------------

st.set_page_config(page_title="Gen 14.2 (Final)", layout="wide", page_icon="✨")
st.title("✨ Генератор 14.2: Исправленный")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ ---
def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        timeout = 60 if width > 1024 else 30
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

# --- Вкладки ---
tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# === 1. ГЕНЕРАТОР ===
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        # ОБРАТИТЕ ВНИМАНИЕ: Я обернул вводы в st.form, чтобы все работало корректно
        with st.form("gen_form"):
            mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=100)
            # Теперь кнопка внутри формы, как и положено
            submit = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submit and user_input:
            # Промпт
            translator = GoogleTranslator(source='auto', target='en')
            scene_en = translator.translate(user_input)
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            if "Самокат" in mode:
                raw_prompt = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
                
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            with st.spinner("Рисую эскиз..."):
                img_bytes = generate_image(final_prompt, w, h, seed)

            if img_bytes == "BUSY":
                st.warning("Сервер перегружен. Нажмите кнопку еще раз.")
            elif img_bytes:
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, caption=f"Результат ({w}x{h})", use_container_width=True)
                
                # Сохранение
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                final_filename = f"{timestamp}_{seed}_{w}_{h}.png"
                filepath = os.path.join(GALLERY_DIR, final_filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                # Сохраняем промпт
                with open(filepath + ".txt", "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                    
                st.toast("✅ Сохранено!")
                time.sleep(1)
                st.rerun()

# === 2. ГАЛЕРЕЯ ===
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    
    if not files:
        st.info("Галерея пуста.")
    else:
        st.write(f"Всего изображений: {len(files)}")
        cols = st.columns(2)
        
        for i, filename in enumerate(files):
            filepath = os.path.join(GALLERY_DIR, filename)
            txt_path = filepath + ".txt"
            
            # Читаем параметры
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
                width = int(parts[2])
                height = int(parts[3])
                is_4k = width > 1500
            except:
                seed = 0; width = 1024; is_4k = False

            with cols[i % 2]:
                with st
