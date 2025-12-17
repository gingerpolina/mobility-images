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

st.set_page_config(page_title="Urent Gen v18 (Final Fix)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v18: Стабильная + Синий Фон")

# Инициализация памяти сессии (чтобы картинка не пропадала)
if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (АГРЕССИВНЫЙ ПЛАСТИК)
# ==========================================

# СТИЛЬ: Жесткий запрет на реализм
STYLE_PREFIX = (
    "((NO REALISM)). ((Matte Plastic Toy World)). ((3D Claymorphism)). "
    "LOOK: Cute, Minimalist, Smooth rounded edges, Play-Doh texture. "
    "MATERIAL: Soft-touch matte plastic everywhere. "
    "LIGHTING: Bright Softbox lighting, clean shadows. "
)

STYLE_SUFFIX = "Everything is made of matte plastic. Unreal Engine 5. Blender 3D."

# АНАТОМИЯ: СКЕЙТ С РУЧКОЙ (Хак против сидений)
SCOOTER_CORE = (
    "OBJECT: A modern Stand-up Electric Kickboard. "
    "ANATOMY: A flat skateboard-like deck (Snow White) + A vertical T-bar handle (Royal Blue). "
    "((STRICTLY NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). "
    "The object is designed for STANDING only. "
)

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# ЦВЕТА
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Details (#FF9601). NO PINK."

# НЕГАТИВ (Усиленный вес против сидений и фото)
NEGATIVE_PROMPT = "(seat:3.0), (saddle:3.0), (chair:3.0), moped, vespa, motorcycle, realistic, photo, metal, chrome, reflection, dirt, grunge, pink, purple, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    # Формируем URL
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    
    try:
        # Тайм-аут: 80 сек для больших (HD), 30 для маленьких
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
            
            # ВЫБОР ФОНА
            bg_select = st.selectbox("Фон:", [
                "⬜ Студийный Белый", 
                "🟦 Студийный Синий (#0668D7)",
                "🏙️ Улица (Размытая)", 
                "🌳 Парк (Зелень)", 
                "🌃 Ночной Город (Киберпанк)"
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
            
            # 2. Настройка фона (через if/elif)
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

            # 3. Сборка промпта
            if "Самокат" in mode:
                # Добавляем контекст скейта
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

            # 5. Запрос
            with st.spinner("Генерация..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят (429). Подождите 5 секунд.")
            elif img_bytes:
                # СОХРАНЕНИЕ В ПАМЯТЬ СЕССИИ (чтобы не исчезло)
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                # СОХРАНЕНИЕ НА ДИСК (для галереи)
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = f"{t_str}_{seed}_{w}_{h}.png"
                fp = os.path.join(GALLERY_DIR, fn)
                
                with open(fp, "wb") as f: 
                    f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f: 
                    f.write(final_prompt)
                
                # Перезагрузка страницы для обновления галереи
                st.rerun()
            else:
                st.error("Ошибка сети.")

        # БЛОК ОТОБРАЖЕНИЯ (вне логики кнопки, работает всегда при наличии данных)
        if st.session_state.last_image_bytes:
            st.success("Готово!")
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption=f"Результат ({st.session_state.last_image_size[0]}x{st.session_state.last_image_size[1]})", use_container_width=True)

# --- ВКЛАДКА 2: ГАЛЕРЕЯ ---
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    if not files:
        st.info("Галерея пуста.")
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

                    # Метки качества (Safe HD)
                    if rw > 1400:
                        st.caption(f"💎 **Safe HD** ({rw}x{rh})")
                        can_up = False
                    else:
                        st.caption(f"🔹 Base ({rw}x{rh})")
                        can_up = True
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    # Кнопка Скачать
                    with open(fp, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"d{i}")
                    
                    # Кнопка Safe Upscale (1536px)
                    if can_up:
                        if c2.button("✨ HD (Safe)", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f: p = f.read()
                                
                                with st.spinner("Улучшаю до 1536px..."):
                                    # Целимся в 1536px
                                    hq = generate_image(p, 1536, 1536, seed)
                                    if hq and hq != "BUSY":
                                        check = Image.open(io.BytesIO(hq))
                                        cw, ch = check.size
                                        
                                        if cw < 1400:
                                            st.warning(f"Сервер не смог выдать HD (прислал {cw}x{ch}).")
                                        else:
                                            # Заменяем файл
                                            n_name = filename.replace(f"_{rw}_{rh}", f"_{cw}_{ch}")
                                            n_path = os.path.join(GALLERY_DIR, n_name)
                                            with open(n_path, "wb") as f: f.write(hq)
                                            shutil.copy(tp, n_path + ".txt")
                                            
                                            os.remove(fp)
                                            os.remove(tp)
                                            st.rerun()
                                    else:
                                        st.error("Сервер занят.")
                            else: st.error("Нет данных.")
                    
                    # Кнопка Удалить
                    if c3.button("🗑️", key=f"x{i}"):
                        os.remove(fp)
                        if os.path.exists(tp): os.remove(tp)
                        st.rerun()
