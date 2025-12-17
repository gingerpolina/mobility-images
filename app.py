import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- НАСТРОЙКИ СТИЛЯ (MAXIMUM PLASTIC) ---

# 1. ГЛАВНЫЙ СТИЛЬ: Заставляем все выглядеть как 3D-иконку, а не фото.
STYLE_HEADER = """
((3D Render)), ((Claymorphism Style)), ((Cute 3D Icon)).
MATERIAL: ((Matte Plastic)), ((Soft Rubber)), ((Play-Doh)).
SHAPES: ((Smooth)), ((Rounded)), ((Bubble-like)), ((Geometric)), ((Minimalist)).
DETAILS: Low detail, no textures, no noise.
"""

# 2. ФОН: Жестко белый, без углов комнаты.
BACKGROUND_RULE = """
BACKGROUND: ((PURE WHITE HEX #FFFFFF)), ((FLAT 2D)), ((ISOLATED)). 
LIGHTING: Soft studio lighting from top-left. NO CAST SHADOWS.
"""

# 3. ЦВЕТА
COLOR_RULES = """
PALETTE:
- Main Object: Snow White (#EAF0F9) & Royal Blue (#0668D7).
- Accents: Orange (#FF9601).
FORBIDDEN: ((Pink)), ((Purple)), ((Realism)), ((Dirt)).
"""

# 4. ОБЪЕКТЫ
SCOOTER_CORE = "OBJECT: A cute stylized Electric Kickboard (scooter). Vertical stem, flat deck. ((NO SEAT))."
CAR_CORE = "OBJECT: A cute stylized White Sedan car with blue stripes."

# 5. НЕГАТИВНЫЙ ПРОМПТ (Убиваем комнату и текстуры)
NEGATIVE_PROMPT = """
room, wall, floor, corner, architecture, interior,
photorealistic, 8k, photography, 
texture, fur, needles, hair, grain, noise,
shadow, ambient occlusion, dark,
pink, magenta, purple
"""

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 5.0 (Final Polish)", layout="centered", page_icon="🎨")
st.title("🎨 Генератор 5.0: Гладкий пластик")
st.caption("Исправлено: фон теперь идеально белый (без стен), елки — гладкие (без иголок).")

with st.sidebar:
    use_turbo = st.checkbox("Turbo-режим", value=False)
    model = "turbo" if use_turbo else "flux"

mode = st.radio("Тип объекта:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с елкой", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Леплю из цифрового пластилина...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. ТРАНСФОРМАЦИЯ СЦЕНЫ (Самое важное!)
        # Превращаем "Елку" в "Абстрактную геометрическую форму"
        stylized_scene = f"abstract smooth geometric 3d version of {scene_en}, made of smooth matte plastic, rounded edges"
        
        # 3. СБОРКА ПРОМПТА
        if "Самокат" in mode:
            safe_scene = stylized_scene.replace("scooter", "").replace("bike", "")
            final_prompt = f"{STYLE_HEADER} {SCOOTER_CORE} SCENE: {safe_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
            
        elif "Машина" in mode:
            final_prompt = f"{STYLE_HEADER} {CAR_CORE} SCENE: {stylized_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
            
        else:
            final_prompt = f"{STYLE_HEADER} OBJECT: {stylized_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
        
        # Добавляем негативный промпт
        final_prompt += f" --no {NEGATIVE_PROMPT}"

        # 4. Отправка
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 99999)
        
        # enhance=false ОБЯЗАТЕЛЬНО, иначе он сам дорисует реалистичные текстуры
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
        
        # Запрос с повтором
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            time.sleep(2)
            response = requests.get(url, timeout=60)

        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            st.success("Готово!")
            st.image(image, caption="Результат (Стиль: Matte Plastic)", use_container_width=True)
            
            with st.expander("Как мы описали это для нейросети?"):
                st.write(final_prompt)
                
            st.download_button("Скачать PNG", image_data, "brand_final.png", "image/png")
        else:
            st.error("Ошибка сервера. Попробуйте еще раз.")

    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
