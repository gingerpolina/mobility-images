import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
# Если deep_translator не установлен, код не упадет, а использует заглушку
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

import random
import time
import os
import datetime

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v31 (Unibody)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v31: Монолитный Дизайн")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК
# ==========================================

# СТИЛЬ: Matte Plastic + Claymorphism
STYLE_PREFIX = "((NO REALISM)). 3D minimalist product render. Style: Matte plastic textures, smooth rounded shapes, soft studio lighting, ambient occlusion. Aesthetic: Playful, modern, high fidelity, C4D style, Octane render."

STYLE_SUFFIX = "High quality 3D render. 4k resolution."

# КОМПОЗИЦИЯ
COMPOSITION_RULES = "COMPOSITION: Whole object strictly inside frame. Wide margins. Zoom out. Centered."

# АНАТОМИЯ (ОБНОВЛЕННАЯ - UNIBODY)
# Мы описываем деку как единый литой элемент со встроенными колесами.
SCOOTER_CORE = (
    "MAIN OBJECT: Modern Electric Kick Scooter. "
    "DESIGN RULES: 1. A tall vertical Blue tube (Steering stem) with T-handlebars. "
    "2. A wide, seamless, low-profile unibody standing deck (Snow White). "
    "3. Small minimalist wheels are partially enclosed within the deck housing. "
    "SHAPE: Sleek, integrated, geometric L-shape. ((NO SEAT))."
)

CAR_CORE = "MAIN OBJECT: Cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."

# ЦВЕТА
COLOR_RULES = "COLORS: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."

NEGATIVE_PROMPT = "realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, moped, motorcycle, bulky battery, wires, cut off, cropped, text, watermark"

# ==========================================
# 3. ФУНКЦИИ (С ЗАЩИТОЙ)
# ==========================================

def make_request_with_retry(url, max_retries=3):
    """Пытается скачать картинку несколько раз, если сервер занят."""
    for attempt in range(max_retries):
        try:
            # Тайм-аут 45 секунд
            response = requests.get(url, timeout=45)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 429:
                time.sleep(2 + attempt * 2) # Ждем 2, 4, 6 сек
                continue # Пробуем снова
        except requests.exceptions.RequestException:
            time.sleep(2 + attempt * 2)
            continue
    return None

def generate_image(prompt, width, height, seed, model='flux'):
    # Собираем URL
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=true&seed={seed}"
    
    return make_request_with_retry(url)

def smart_resize(image_bytes, target_w, target_h):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        current_w, current_h = img.size
        # Если картинка меньше целевой, увеличиваем качественно
        if current_w < target_w or current_h < target_h:
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        return image_bytes

def translate_text(text):
    if not text or not HAS_TRANSLATOR:
        return text
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except:
        return text

# ==========================================
# 4. ИНТЕРФЕЙС
# ==========================================

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            passenger_input = st.text_input("👤 Пассажир:", placeholder="Например: Кот...")
            
            st.divider()
            
            color_theme = st.selectbox("🎨 Окружение:", [
                "🟦 Urent Blue (Синий монохром)", 
                "⬜ Flat White (Белый минимализм)", 
                "🟧 Urent Orange (Оранжевый)",
                "🎨 Natural (Естественные цвета)",
                "⬛ Matte Black (Черный)"
            ])
            
            env_input = st.text_area("🌳 Детали окружения:", height=80, placeholder="Например: елки...")
            aspect = st.selectbox("Формат:", ["1:1", "16:9", "9:16"])
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # 1. Перевод
            env_en = translate_text(env_input) if env_input else ""
            pass_en = translate_text(passenger_input) if passenger_input else ""

            # 2. Пассажир
            if pass_en:
                passenger_prompt = "RIDER: A cute 3D plastic toy character of " + pass_en + " standing on the deck."
            else:
                passenger_prompt = "No rider. Empty deck. ((NO SEAT))."

            # 3. Фон и Материалы
            if "Blue" in color_theme:
                bg_data = "BACKGROUND: Solid Royal Blue #0668D7. ENVIRONMENT MATERIAL: Matte Royal Blue Plastic."
            elif "Orange" in color_theme:
                bg_data = "BACKGROUND: Solid Neon Orange #FF9601. ENVIRONMENT MATERIAL: Matte Orange Plastic."
            elif "White" in color_theme:
                bg_data = "BACKGROUND: Solid Flat White. ENVIRONMENT MATERIAL: Matte White Plastic."
            elif "Black" in color_theme:
                bg_data = "BACKGROUND: Solid Matte Black. ENVIRONMENT MATERIAL: Dark Grey Plastic."
            else:
                bg_data = "BACKGROUND: Studio Lighting. ENVIRONMENT MATERIAL: Colorful matte plastic."

            if env_en:
                full_env = "SCENE: " + env_en + ". " + bg_data
            else:
                full_env = "SCENE: Isolated studio shot. " + bg_data

            # 4. Сборка
            if "Самокат" in mode: core = SCOOTER_CORE
            elif "Машина" in mode: core = CAR_CORE
            else: core = "MAIN OBJECT: " + env_en

            # Собираем строку через плюс (самый надежный способ)
            raw_prompt = STYLE_PREFIX + " " + COMPOSITION_RULES + " " + core + " " + passenger_prompt + " " + full_env + " " + COLOR_RULES + " " + STYLE_SUFFIX
            
            final_prompt = raw_prompt + " --no " + NEGATIVE_PROMPT
            
            # Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 5. Запуск
            status_box = st.empty()
            status_box.info("🔄 Стучимся к серверу (3 попытки)...")
            
            img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes:
                status_box.success("✅ Готово!")
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                # Сохранение
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = f"{t_str}_{seed}_{w}_{h}.png"
                fp = os.path.join(GALLERY_DIR, fn)
                
                with open(fp, "wb") as f: f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f: f.write(final_prompt)
                
                time.sleep(0.5)
                st.rerun()
            else:
                status_box.error("❌ Сервер перегружен. Нажмите кнопку еще раз.")

        if st.session_state.last_image_bytes:
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption="Результат", use_container_width=True)

with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    if not files:
        st.info("Галерея пуста.")
    else:
        st.write(f"Работ: {len(files)}")
        cols = st.columns(2)
        for i, filename in enumerate(files):
            fp = os.path.join(GALLERY_DIR, filename)
            tp = fp + ".txt"
            
            with cols[i % 2]:
                with st.container(border=True):
                    try: 
                        img = Image.open(fp)
                        st.image(img)
                    except: continue
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    with open(fp, "rb") as f: c1.download_button("⬇️", f, filename)
                    
                    # Кнопка Апскейла
                    rw, rh = img.size
                    if rw < 2000:
                        if c2.button("✨ 2048px", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f: p = f.read()
                                st.toast("⏳ Улучшаем...")
                                try:
                                    # Парсим seed из имени файла, если есть
                                    old_seed = int(filename.split("_")[1])
                                except:
                                    old_seed = random.randint(1, 99999)

                                hq_bytes = generate_image(p, 2048, 2048, old_seed)
                                if hq_bytes:
                                    final_bytes = smart_resize(hq_bytes, 2048, 2048)
                                    n_path = os.path.join(GALLERY_DIR, filename.replace(f"_{rw}_{rh}", "_2048_2048"))
                                    with open(n_path, "wb") as f: f.write(final_bytes)
                                    shutil.copy(tp, n_path + ".txt")
                                    os.remove(fp)
                                    os.remove(tp)
                                    st.rerun()
                                else:
                                    st.error("Сервер занят")
                            else: st.error("Нет промпта")
                    
                    if c3.button("🗑️", key=f"x{i}"):
                        os.remove(fp)
                        if os.path.exists(tp): os.remove(tp)
                        st.rerun()
