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

st.set_page_config(page_title="Urent Gen v29 (Smart Rev)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v29: Умная Ревизия")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (МЯГКАЯ СИЛА)
# ==========================================

# СТИЛЬ: Больше воздуха, меньше агрессии. Описываем желанный результат.
STYLE_PREFIX = (
    "((NO REALISM)). A high-quality 3D minimalist render in a matte plastic toy world style. "
    "Claymorphism aesthetic, smooth rounded geometric shapes, soft-touch materials. "
    "Clean studio lighting, gentle soft shadows, ambient occlusion. "
    "Playful, modern, friendly vibe. "
)

STYLE_SUFFIX = "Detailed 3D render. 4k resolution."

# КОМПОЗИЦИЯ: Конкретные инструкции про отступы
COMPOSITION_RULES = (
    "COMPOSITION: The entire object is centered and fully contained within the canvas. "
    "Generous margins on all sides (top, bottom, left, right). "
    "Nothing is cropped or cut off by the frame edges. "
)

# АНАТОМИЯ САМОКАТА (Описательная, а не запретительная)
# Мы описываем "стоячий" дизайн так подробно, что сиденью некуда встать.
SCOOTER_CORE = (
    "MAIN OBJECT: A modern industrial design concept of an Electric Kick Scooter meant for standing. "
    "FORM FUNCTION: A tall, thick, vertical steering column (Royal Blue) connected to a long, low, wide, perfectly flat standing deck (Snow White). "
    "Minimalist enclosed wheels. The deck is empty and flat, designed for a standing rider. "
)

CAR_CORE = "MAIN OBJECT: A cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."

# ЦВЕТА: Глобальные правила
COLOR_RULES = "GLOBAL COLORS: Matte Snow White (#EAF0F9), Royal Blue (#0668D7), Neon Orange (#FF9601). NO PINK."

# НЕГАТИВ: Убираем лишнее, но без истерики
NEGATIVE_PROMPT = (
    "realistic, photo, grain, noise, dirt, metal reflection, "
    "seat, saddle, chair, bench, moped, motorcycle, "
    "cropped, cut off, out of frame, partially visible, "
    "text, watermark, low quality"
)

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    # Используем enhance=true для попытки поднять детализацию самоката
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=true&seed={seed}"
    try:
        timeout_val = 90 if width > 1200 else 40
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
            mode = st.radio("Транспорт:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            passenger_input = st.text_input("👤 Пассажир (Пусто = без никого):", placeholder="Например: Кот в шлеме...")
            st.divider()
            color_theme = st.selectbox("🎨 Палитра окружения:", [
                "🟦 Urent Blue (Синий монохром)", 
                "⬜ Flat White (Белый минимализм)", 
                "🟧 Urent Orange (Оранжевый взрыв)",
                "🎨 Natural (Естественные цвета)",
                "⬛ Matte Black (Черный стиль)"
            ])
            env_input = st.text_area("🌳 Детали окружения (Пусто = чистая студия):", height=80, placeholder="Например: елки, городские улицы...")
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # === ПЕРЕВОД ===
            translator = GoogleTranslator(source='auto', target='en')
            env_en = translator.translate(env_input) if env_input else ""
            
            if passenger_input:
                pass_en = translator.translate(passenger_input)
                passenger_prompt = f"RIDER: A cute 3D plastic toy character of {pass_en} standing on the deck."
            else:
                # Мягкое напоминание об отсутствии сиденья
                passenger_prompt = "No rider. The deck is empty and flat. (No seat)."

            # === НОВАЯ ЛОГИКА ОКРУЖЕНИЯ (Спасение елок) ===
            
            # Определение материалов окружения на основе темы
            if "Blue" in color_theme:
                env_style_directive = "All environmental elements are rendered in monochrome Matte Royal Blue plastic."
                bg_directive = "seamless blue studio cyclorama"
            elif "Orange" in color_theme:
                env_style_directive = "All environmental elements are rendered in monochrome Matte Neon Orange plastic."
                bg_directive = "seamless orange studio cyclorama"
            elif "White" in color_theme:
                env_style_directive = "All environmental elements are rendered in monochrome Matte White plastic."
                bg_directive = "seamless white studio cyclorama"
            elif "Black" in color_theme:
                env_style_directive = "All environmental elements are rendered in monochrome Matte Black plastic."
                bg_directive = "seamless black studio cyclorama"
            else: # Natural
                env_style_directive = "Environmental elements have colorful matte plastic toy look."
                bg_directive = "soft studio gradient background"

            # Формирование блока окружения
            if env_en:
                # Если есть описание, мы интегрируем его с материалами и фоном
                full_env_prompt = f"ENVIRONMENT SCENE: {env_en}. {env_style_directive} The scene is set against a {bg_directive}."
            else:
                # Если описания нет, просто чистый фон
                full_env_prompt = f"ENVIRONMENT: Isolated studio shot against a clean {bg_directive}. No other objects."

            # === СБОРКА ===
            if "Самокат" in mode: core_obj = SCOOTER_CORE
            elif "Машина" in mode: core_obj = CAR_CORE
            else: core_obj = f"MAIN OBJECT: {env_en}" if env_en else "MAIN OBJECT: Abstract plastic shape"

            # Важный порядок: Стиль -> Композиция -> Объект -> Пассажир -> ОКРУЖЕНИЕ -> Цвета -> Суффикс
            # Окружение теперь стоит ДО глобальных правил цвета, чтобы его не затерло.
            
            part1 = STYLE_PREFIX + " " + COMPOSITION_RULES + " "
            part2 = core_obj + " " + passenger_prompt + " "
            part3 = full_env_prompt + " " + COLOR_RULES + " " + STYLE_SUFFIX
            
            raw_prompt = part1 + part2 + part3
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # Размеры
            base_s = 1024 
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # === ГЕНЕРАЦИЯ ===
            with st.spinner("Рендер сцены (может занять минуту)..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер перегружен (429). Попробуйте позже.")
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
                st.error("Ошибка сети или тайм-аут.")

        if st.session_state.last_image_bytes:
            st.success("Готово!")
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption=f"Результат ({st.session_state.last_image_size[0]}x{st.session_state.last_image_size[1]})", use_container_width=True)

# --- ГАЛЕРЕЯ ---
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
            try: seed = int(filename.replace(".png", "").split("_")[1])
            except: seed = 0
            
            with cols[i % 2]:
                with st.container(border=True):
                    try: img = Image.open(fp); st.image(img)
                    except: continue
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    with open(fp, "rb") as f: c1.download_button("⬇️", f, filename)
                    
                    rw, rh = img.size
                    if rw < 2000:
                        if c2.button("✨ 2048px", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f: p = f.read()
                                with st.spinner("Апскейл..."):
                                    hq = generate_image(p, 2048, 2048, seed)
                                    if hq and hq != "BUSY":
                                        final = smart_resize(hq, 2048, 2048)
                                        n_path = os.path.join(GALLERY_DIR, filename.replace(f"_{rw}_{rh}", "_2048_2048"))
                                        with open(n_path, "wb") as f: f.write(final)
                                        shutil.copy(tp, n_path + ".txt")
                                        os.remove(fp); os.remove(tp)
                                        st.rerun()
                            else: st.error("Ошибка")
                    if c3.button("🗑️", key=f"x{i}"):
                        os.remove(fp); 
                        if os.path.exists(tp): os.remove(tp)
                        st.rerun()
