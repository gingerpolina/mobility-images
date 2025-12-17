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

st.set_page_config(page_title="Gen 14.1 (Fixed)", layout="wide", page_icon="✨")
st.title("✨ Генератор 14.1: Исправленный")

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
        mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
        aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
        user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=100)
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
                st.warning("Сервер перегружен. Нажмите еще раз.")
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

# === 2. ГАЛЕРЕЯ (ИСПРАВЛЕННАЯ ЛОГИКА) ===
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
            
            # Читаем параметры из имени файла
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
                width = int(parts[2])
                height = int(parts[3])
                is_4k = width > 1500
            except:
                seed = 0; width = 1024; is_4k = False

            with cols[i % 2]:
                with st.container(border=True):
                    # Открываем картинку (БЕЗ ГИГАНТСКОГО TRY/EXCEPT)
                    try:
                        img = Image.open(filepath)
                        st.image(img, use_container_width=True)
                    except Exception as e:
                        st.error(f"Ошибка чтения файла: {filename}")
                        continue # Пропускаем остальное, если файл битый

                    # Подписи и Кнопки
                    if is_4k:
                        st.caption(f"💎 **Ultra HD** | {width}x{height}")
                    else:
                        st.caption(f"🔹 Standard | {width}x{height}")
                    
                    c1, c2 = st.columns(2)
                    
                    # Кнопка СКАЧАТЬ
                    with open(filepath, "rb") as f:
                        c1.download_button("⬇️ Скачать", f, filename, "image/png", key=f"dl_{filename}")

                    # Кнопка УЛУЧШИТЬ
                    if not is_4k:
                        if c2.button("✨ В 4K", key=f"up_{filename}"):
                            if os.path.exists(txt_path):
                                with open(txt_path, "r", encoding="utf-8") as f:
                                    saved_prompt = f.read()
                                
                                with st.spinner("⏳ Делаю 4K (40 сек)..."):
                                    new_w, new_h = width * 2, height * 2
                                    hq_bytes = generate_image(saved_prompt, new_w, new_h, seed)
                                    
                                    if hq_bytes and hq_bytes != "BUSY":
                                        # Замена файла
                                        new_name = filename.replace(f"_{width}_{height}", f"_{new_w}_{new_h}")
                                        new_path = os.path.join(GALLERY_DIR, new_name)
                                        
                                        with open(new_path, "wb") as f: f.write(hq_bytes)
                                        shutil.copy(txt_path, new_path + ".txt")
                                        
                                        os.remove(filepath)
                                        os.remove(txt_path)
                                        st.rerun()
                                    else:
                                        st.error("Сервер занят, попробуйте позже.")
                            else:
                                st.error("Нет файла промпта.")
                    
                    # Кнопка УДАЛИТЬ
                    if st.button("🗑️ Удалить", key=f"del_{filename}"):
                        os.remove(filepath)
                        if os.path.exists(txt_path): os.remove(txt_path)
                        st.rerun()
