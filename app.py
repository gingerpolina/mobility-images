import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- НАСТРОЙКИ 7.0 (PREMIUM MINIMALISM) ---

# 1. СТИЛЬ: "Дорогой" матовый материал, но без лишнего реализма.
# Soft-Touch = приятный на ощупь матовый пластик.
STYLE_HEADER = """
((3D Minimalist Render)), ((Product Visualization)).
MATERIAL: ((Matte Soft-Touch Plastic)), ((Ceramic finish)), ((Clean)).
STYLE: Apple-like minimalism, smooth geometry, chamfered edges.
LIGHTING: Softbox studio lighting, even illumination, no harsh shadows.
"""

# 2. ФОН: Бесконечный белый.
BACKGROUND_RULE = """
BACKGROUND: ((PURE WHITE HEX #FFFFFF)), ((Infinite Studio Background)). 
No floor texture, no horizon line.
"""

# 3. ЦВЕТА: Четкое разделение зон (Color Blocking).
COLOR_RULES = """
COLOR PALETTE:
- CHASSIS (Deck & Frame): Matte Snow White.
- STEM (Pole): Deep Royal Blue (#0668D7).
- ACCENTS (Wires/Reflectors): Vibrant Safety Orange (#FF9601).
- TIRES: Matte Dark Grey.
"""

# 4. АНАТОМИЯ САМОКАТА (ИНЖЕНЕРНАЯ ТОЧНОСТЬ)
# Dashboard убрали. Добавили "Tubular" и "Unibody", чтобы собрать форму.
SCOOTER_CORE = """
OBJECT: A modern Electric Kick Scooter.
GEOMETRY:
- Thick tubular vertical stem (steering column).
- Wide flat unibody deck (footboard).
- Minimalist rear fender.
- Integrated cable routing.
- ((NO SEAT)), ((NO SADDLE)). It is strictly for standing.
"""

# 5. АНАТОМИЯ МАШИНЫ
CAR_CORE = "OBJECT: A modern autonomous white sedan car with blue branding strip. Smooth minimalist shape."

# 6. НЕГАТИВНЫЙ ПРОМПТ
NEGATIVE_PROMPT = """
dashboard, screen, display, complex details, wires,
shiny metal, chrome, reflection,
seat, saddle, bicycle, moped, motorcycle,
toy, low poly, pixelated, 
pink, purple, red, green,
shadow, dirt, grunge
"""

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 7.0 (Clean Shape)", layout="centered", page_icon="✨")
st.title("✨ Генератор 7.0: Чистая Форма")
st.caption("Фокус на правильной геометрии (Tubular/Unibody) и материалах Soft-Touch.")

with st.sidebar:
    use_turbo = st.checkbox("Turbo-режим", value=False)
    model = "turbo" if use_turbo else "flux"

mode = st.radio("Тип объекта:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Рендер формы...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. ТРАНСФОРМАЦИЯ СЦЕНЫ
        # Добавляем "Minimalist composition", чтобы фон не перегружался
        stylized_scene = f"minimalist composition, {scene_en}, clean forms"
        
        # 3. СБОРКА ПРОМПТА
        if "Самокат" in mode:
            safe_scene = stylized_scene.replace("scooter", "").replace("bike", "")
            final_prompt = f"{STYLE_HEADER} {SCOOTER_CORE} {COLOR_RULES} SCENE: {safe_scene}. {BACKGROUND_RULE}"
            
        elif "Машина" in mode:
            final_prompt = f"{STYLE_HEADER} {CAR_CORE} {COLOR_RULES} SCENE: {stylized_scene}. {BACKGROUND_RULE}"
            
        else:
            final_prompt = f"{STYLE_HEADER} OBJECT: {stylized_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
        
        final_prompt += f" --no {NEGATIVE_PROMPT}"

        # 4. Отправка
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 99999)
        
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
        
        # Повторные попытки при ошибке
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            time.sleep(2)
            response = requests.get(url, timeout=60)

        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            st.success("Готово!")
            st.image(image, caption="Результат (Style: Soft-Touch)", use_container_width=True)
            
            with st.expander("Технический промпт"):
                st.write(final_prompt)
                
            st.download_button("Скачать PNG", image_data, "brand_clean.png", "image/png")
        else:
            st.error("Ошибка сервера.")

    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
