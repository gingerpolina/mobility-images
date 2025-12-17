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

st.set_page_config(page_title="Urent Gen v17 (Platinum)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v17: Platinum")

# Инициализация состояния (чтобы картинка не исчезала)
if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. ПАРАМЕТРЫ СТИЛЯ (БРЕНДБУК)
# ==========================================

# СТИЛЬ: Игрушечный мир
STYLE_PREFIX = (
    "((NO REALISM)). ((3D Claymorphism Render)), ((Matte Soft Plastic Material)). "
    "LOOK: Cute, Minimalist, Smooth rounded edges, Toy-like proportions. "
    "LIGHTING: Bright Softbox lighting, clean shadows. "
)

STYLE_SUFFIX = "Everything is made of matte plastic. Unreal Engine 5. Blender 3D."

# АНАТОМИЯ: СКЕЙТ С РУЧКОЙ (Убиваем сиденье)
SCOOTER_CORE = (
    "OBJECT: A modern Stand-up Electric Kickboard. "
    "ANATOMY: A flat skateboard-like deck (Snow White) + A vertical T-bar handle (Royal Blue). "
    "((STRICTLY NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). "
    "The object is designed for STANDING only. "
)

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# ЦВЕТА
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Details (#FF9601). NO PINK."

# НЕГАТИВ (Вес 3.0 на сиденья)
NEGATIVE_PROMPT = "(seat:3.0), (saddle:3.0), (chair:3.0), moped, vespa, motorcycle, realistic, photo, metal, chrome, reflection, dirt, grunge, pink, purple, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        # Для HD даем больше времени
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

# --- Вкладка 1: ГЕНЕРАТОР ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            # ВАРИАТИВНОСТЬ ФОНА
            bg_select = st.selectbox("Фон:", [
                "⬜ Студийный Белый", 
                "🏙️ Улица (Размытая)", 
                "🌳 Парк (Зелень)", 
                "🌃 Ночной Город (Неон)"
            ])
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Детали (например: стоит у столба):", height=80)
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        # БЛОК 1: Логика генерации
        if submitted and user_input:
            # 1. Перевод
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input)
            except:
                scene_en = user_input
            
            # Чистка
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            # 2. Обработка фона
            if "Белый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid White Hex #FFFFFF)). Isolated."
            elif "Улица" in bg_select:
                bg_prompt = "BACKGROUND: Blurred minimalist city street, bokeh, plastic style buildings."
            elif "Парк" in bg_select:
                bg_prompt = "BACKGROUND: Minimalist plastic park, abstract green trees, soft sunlight."
            elif "Ночной" in bg_select:
                bg_prompt = "BACKGROUND: Dark blue night city, soft neon lights, bokeh, plastic style."
            
            # 3. Сборка (через переменные, чтобы не было ошибок синтаксиса)
            if "Самокат" in mode:
                # Добавляем "skater standing" чтобы точно убрать сиденье
                scene_context = f"SCENE: {clean_scene}. The object looks like a skateboard with a handle."
                raw_prompt = f"{STYLE_PREFIX} {SCOOTER_CORE} {scene_context} {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} SCENE: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            with st.spinner("Генерация..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят. Подождите 5 секунд.")
            elif img_bytes:
                # СОХРАНЯЕМ В SESSION STATE (чтобы не пропало)
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                # СОХРАНЯЕМ НА ДИСК
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = f"{t_str}_{seed}_{w}_{h}.png"
                fp = os.path.join(GALLERY_DIR, fn)
                with open(fp, "wb") as f: f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f: f.write(final_prompt)
                
                # Принудительный реран, чтобы обновить Галерею, 
                # но Session State сохранит картинку на экране
                st.rerun() 
            else:
                st.error("Ошибка сети.")

        # БЛОК 2: Отображение последней картинки (из памяти)
        if st.session_state.last_image_bytes:
            st.success("Готово! Картинка сохранена в галерею.")
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption=f"Результат ({st.session_state.last_image_size[0]}x{st.session_state.last_image_size[1]})", use_container_width=True)

# --- Вкладка 2: ГАЛЕРЕЯ ---
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    if not files:
        st.info("Пусто.")
    else:
        st.write(f"Работ в галерее: {len(files)}")
        cols = st.columns(2)
        for i, filename in enumerate(files):
            fp = os.path.join(GALLERY_DIR, filename)
            tp = fp + ".txt"
            
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
            except: seed = 0

            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        img = Image.open(fp)
                        rw, rh = img.size
                        st.image(img, use_container_width=True)
                    except: continue

                    # Статус
                    if rw > 1500:
                        st.caption(f"💎 **Safe HD** ({rw}x{rh})")
                        can_up = False
                    else:
                        st.caption(f"🔹 Base ({rw}x{rh})")
                        can_up = True
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    with open(fp, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"d{i}")
                    
                    if can_up:
                        # ЛОГИКА SAFE UPSCALING (1536px)
                        if c2.button("✨ HD (Safe)", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r") as f: p = f.read()
                                with st.spinner("Улучшаю до 1536px..."):
                                    # Запрашиваем 1536 (компромисс между 1024 и 2048)
                                    hq = generate_image(p, 1536, 1536, seed)
                                    if hq and hq != "BUSY":
                                        # Проверяем размер
                                        check_img = Image.open(io.BytesIO(hq))
                                        cw, ch = check_img.size
                                        
                                        if cw < 1400:
                                            st.warning(f"Сервер не смог выдать HD (прислал {cw}x{ch}).")
                                        else:
                                            n_name = filename.replace(f"_{rw}_{rh}", f"_{cw}_{ch}")
                                            n_path = os.path.join(GALLERY_DIR, n_name)
                                            with open(n_path, "wb") as f: f.write(hq)
                                            shutil.copy(tp, n_path + ".txt")
                                            os.remove(fp); os.remove(tp)
                                            st.rerun()
                                    else:
                                        st.error("Сервер занят.")
                            else: st.error("Нет данных.")
                    
                    if c3.button("🗑️", key=f"x{i}"):
                        os.remove(fp)
                        if os.path.exists(tp): os.remove(tp)
                        st.rerun()
