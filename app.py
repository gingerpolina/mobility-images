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

# --- 1. ПАПКИ ---
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Gen 15.2 (Final)", layout="wide", page_icon="✨")
st.title("✨ Генератор 15.2: Финальный")

# --- 2. СТИЛИ И КОНСТАНТЫ ---
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

# --- 3. ФУНКЦИЯ ГЕНЕРАЦИИ ---
def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        # Тайм-аут: 60 сек для больших, 30 для маленьких
        t_val = 60 if width > 1024 else 30
        response = requests.get(url, timeout=t_val)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

# --- 4. ИНТЕРФЕЙС ---
tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# === ВКЛАДКА 1: ГЕНЕРАТОР ===
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # ФОРМА ВВОДА
        with st.form("generation_form"):
            mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=100)
            
            # Кнопка внутри формы!
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted and user_input:
            # 1. Перевод
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input)
            except:
                scene_en = user_input
            
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            # 2. Сборка промпта (разбил на части, чтобы не ломалось)
            if "Самокат" in mode:
                part1 = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES}"
                part2 = f"SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
            elif "Машина" in mode:
                part1 = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES}"
                part2 = f"SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
            else:
                part1 = f"{STYLE_PREFIX} OBJECT: {clean_scene}."
                part2 = f"{COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
                
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 3. Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 4. Запуск
            with st.spinner("Рисую..."):
                img_bytes = generate_image(final_prompt, w, h, seed)

            if img_bytes == "BUSY":
                st.warning("Сервер перегружен. Нажмите кнопку еще раз.")
            elif img_bytes:
                # Показываем
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, caption=f"Результат ({w}x{h})", use_container_width=True)
                
                # Сохраняем (исправленный формат времени)
                t_str = datetime.datetime.now().strftime("%H%M%S")
                final_filename = f"{t_str}_{seed}_{w}_{h}.png"
                filepath = os.path.join(GALLERY_DIR, final_filename)
                
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                
                with open(filepath + ".txt", "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                    
                st.toast("✅ Сохранено в галерею!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Ошибка соединения.")

# === ВКЛАДКА 2: ГАЛЕРЕЯ ===
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    
    if not files:
        st.info("Галерея пуста.")
    else:
        st.write(f"Сохранено работ: {len(files)}")
        cols = st.columns(2)
        
        for i, filename in enumerate(files):
            filepath = os.path.join(GALLERY_DIR, filename)
            txt_path = filepath + ".txt"
            
            # Читаем параметры из имени файла
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
