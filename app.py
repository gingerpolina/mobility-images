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

st.set_page_config(page_title="Urent Gen v27 (Art Director)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v27: Art Director")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК (ОБНОВЛЕННЫЙ)
# ==========================================

# СТИЛЬ: Тот самый оригинальный, но с защитой
STYLE_PREFIX = (
    "((NO REALISM)). style of 3D minimalist illustration, matte plastic textures, "
    "smooth rounded shapes, soft studio lighting, ambient occlusion, vibrant colors, "
    "clean solid background, Octane render, high fidelity, 3D claymorphism, "
    "playful and modern aesthetic, C4D style. "
)

STYLE_SUFFIX = "High quality 3D render. 4k."

# КОМПОЗИЦИЯ: Zoom Out, чтобы не резались края
COMPOSITION_RULES = (
    "((Whole object strictly inside frame)). ((Wide margins)). ((Zoom out)). "
    "((Plenty of negative space around the object)). "
    "Nothing is cut off by the borders. Centered composition. "
)

# АНАТОМИЯ
SCOOTER_CORE = (
    "MAIN OBJECT: A cute thick Electric Kickboard. "
    "DESIGN: Thick vertical blue tube stem, wide flat white deck, minimalist enclosed wheels. "
    "SHAPE: Geometric, sturdy, robust. ((NO SEAT)). "
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
            passenger_input = st.text_input("👤 Пассажир (Пусто = без никого):", placeholder="Например: Дед Мороз, Кот...")
            
            st.divider()
            
            # 3. Цветовая гамма (Новое!)
            color_theme = st.selectbox("🎨 Палитра окружения:", [
                "🟦 Urent Blue (Синий монохром)", 
                "⬜ Flat White (Белый минимализм)", 
                "🟧 Urent Orange (Оранжевый взрыв)",
                "🎨 Natural (Естественные цвета)",
                "⬛ Matte Black (Черный стиль)"
            ])
            
            # 4. Окружение
            env_input = st.text_area("🌳 Окружение (Пусто = студийный фон):", height=80, placeholder="Например: елки, подарочные коробки...")
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # === 1. ПЕРЕВОД ===
            translator = GoogleTranslator(source='auto', target='en')
            
            # Окружение
            if env_input:
                try: env_en = translator.translate(env_input)
                except: env_en = env_input
            else:
                env_en = "" # Пустое окружение

            # Пассажир
            if passenger_input:
                try: pass_en = translator.translate(passenger_input)
                except: pass_en = passenger_input
                passenger_prompt = f"RIDER: A cute 3D plastic toy character of {pass_en} is standing on the deck."
            else:
                passenger_prompt = "No rider, empty vehicle. ((NO SEAT))."

            # === 2. ЛОГИКА ОКРУЖЕНИЯ И ЦВЕТА ===
            
            if "Blue" in color_theme:
                bg_color = "Solid Royal Blue Hex #0668D7"
                env_material = "Matte Royal Blue Plastic"
            elif "Orange" in color_theme:
                bg_color = "Solid Neon Orange Hex #FF9601"
                env_material = "Matte Orange Plastic"
            elif "White" in color_theme:
                bg_color = "Solid Flat White"
                env_material = "Matte White Plastic"
            elif "Black" in color_theme:
                bg_color = "Solid Matte Black"
                env_material = "Dark Grey Plastic"
            else: # Natural
                bg_color = "Clean Studio Gradient"
                env_material = "Colorful matte plastic"

            if env_en:
                # Если есть описание сцены - красим объекты сцены
                full_env_prompt = f"ENVIRONMENT: {env_en}. All elements are made of {env_material}. BACKGROUND: {bg_color}. Seamless integration."
            else:
                # Если нет описания - просто фон
                full_env_prompt = f"BACKGROUND: {bg_color}. Isolated studio shot. No shadows."

            # === 3. СБОРКА ПРОМПТА ===
            if "Самокат" in mode:
                core_obj = SCOOTER_CORE
            elif "Машина" in mode:
                core_obj = CAR_CORE
            else:
                core_obj = f"MAIN OBJECT: {env_en}" if env_en else "MAIN OBJECT: Abstract shape"

            # Собираем части через плюсы (безопаснее чем f-string для больших блоков)
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

            # === 4. ГЕНЕРАЦИЯ ===
            with st.spinner("Рендер сцены..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят (429).")
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
                    
                    # Кнопка Апскейла
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
