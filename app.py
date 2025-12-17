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
# 1. ЗОЛОТАЯ АРХИТЕКТУРА (КОД НЕ МЕНЯЛСЯ)
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v21 (Art Fix)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v21: Исправление Стиля")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. НОВЫЙ БРЕНДБУК (ПРАВКИ ПРОМПТА)
# ==========================================

# СТИЛЬ: Добавил "Industrial Design" и "Soft Focus", чтобы убрать шум
STYLE_PREFIX = (
    "((NO REALISM)). ((3D Industrial Product Render)), ((Claymorphism)), ((Cute Icon Style)). "
    "LOOK: Smooth matte surfaces, rounded chamfers, minimalist geometry. "
    "MATERIAL: High-quality soft plastic & matte metal. "
    "LIGHTING: Studio softbox, clean white lighting, no hard shadows. "
)

STYLE_SUFFIX = "Rendered in Blender 3D. Unreal Engine 5. Isometric view."

# АНАТОМИЯ: Более конкретные детали, чтобы самокат был "сбитым"
SCOOTER_CORE = (
    "OBJECT: Modern Electric Kick Scooter (Concept Design). "
    "FORM: 1. Thick cylindrical vertical stem (Royal Blue). "
    "2. Wide seamless unibody deck (Snow White). "
    "3. Minimalist wheels with hidden spokes. "
    "((NO SEAT)), ((NO SADDLE)). Structure is strictly L-shaped. "
)

CAR_CORE = "OBJECT: Cute minimalist autonomous white sedan, blue stripe, matte plastic body."

# ЦВЕТА
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."

# НЕГАТИВ
NEGATIVE_PROMPT = "(seat:3.0), (saddle:3.0), bicycle, moped, realistic, photo, wood texture, leaf texture, dirt, grunge, shadow, dark, grain"

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

# --- ВКЛАДКА 1 ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            bg_select = st.selectbox("Студийный Фон:", [
                "⬜ Белый (Flat White)", 
                "🟦 Синий Бренд (#0668D7)",
                "🟧 Оранжевый Бренд (#FF9601)",
                "⬛ Черный Матовый"
            ])
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Детали (например: едет между елками):", height=80)
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # 1. Умный перевод и СТИЛИЗАЦИЯ ВВОДА
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input) if user_input else "studio shot"
            except:
                scene_en = user_input if user_input else "studio shot"
            
            # ВАЖНО: Мы оборачиваем ввод пользователя в "пластиковую" обертку
            # Если пользователь пишет "елки", мы отправляем "low poly plastic toy trees"
            stylized_scene = f"minimalist 3d plastic toy version of {scene_en}, smooth low poly shapes"
            
            # 2. Фон
            if "Белый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat White Color Hex #FFFFFF)). ((2D)). Isolated."
            elif "Синий" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Royal Blue Color Hex #0668D7)). ((2D)). No shadows."
            elif "Оранжевый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Neon Orange Color Hex #FF9601)). ((2D)). No shadows."
            elif "Черный" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Matte Black Color Hex #000000)). ((2D)). No shadows."

            # 3. Сборка
            if "Самокат" in mode:
                # Четкая структура промпта
                raw_prompt = f"{STYLE_PREFIX} {SCOOTER_CORE} SCENE: {stylized_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} SCENE: {stylized_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {stylized_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 4. Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            with st.spinner("Рендер..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят. Подождите пару секунд.")
            elif img_bytes:
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = f"{t_str}_{seed}_{w}_{h}.png"
                fp = os.path.join(GALLERY_DIR, fn)
                
                with open(fp, "wb") as f: f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f: f.write(final_prompt)
                
                st.rerun()
            else:
                st.error("Ошибка сети.")

        if st.session_state.last_image_bytes:
            st.success("Готово!")
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption=f"Результат ({st.session_state.last_image_size[0]}x{st.session_state.last_image_size[1]})", use_container_width=True)

# --- ВКЛАДКА 2 ---
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

                    if rw >= 2000:
                        st.caption(f"💎 **4K (Upscaled)** | {rw}x{rh}")
                        can_up = False
                    else:
                        st.caption(f"🔹 Base | {rw}x{rh}")
                        can_up = True
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    with open(fp, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"d{i}")
                    
                    if can_up:
                        if c2.button("✨ Сделать 2048px", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f: p = f.read()
                                with st.spinner("Запрос 4K + Smart Resize..."):
                                    # Всегда просим 2048
                                    target_w, target_h = 2048, 2048
                                    hq_bytes = generate_image(p, target_w, target_h, seed)
                                    if hq_bytes and hq_bytes != "BUSY":
                                        final_bytes = smart_resize(hq_bytes, target_w, target_h)
                                        n_name = filename.replace(f"_{rw}_{rh}", f"_{target_w}_{target_h}")
                                        n_path = os.path.join(GALLERY_DIR, n_name)
                                        with open(n_path, "wb") as f: f.write(final_bytes)
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
