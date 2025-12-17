import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- НАСТРОЙКИ (АГРЕССИВНЫЙ СТИЛЬ) ---

# Мы используем скобки (( )) для усиления внимания нейросети
STYLE_HEADER = """
((3D Claymorphism Icon)), ((Isometric View)). 
Everything is made of smooth matte plastic. Toy-like proportions. Minimalist shapes.
Lighting: Soft studio lighting, ambient occlusion.
"""

# Жесткое требование к фону
BACKGROUND_RULE = "Background: ((SOLID WHITE COLOR)), ((ISOLATED)), ((NO SHADOWS ON WALL))."

# Цвета (без розового!)
COLOR_RULES = """
COLORS: Main object is Snow White (#EAF0F9) and Royal Blue (#0668D7). 
Accents are Orange (#FF9601).
FORBIDDEN: ((NO PINK)), ((NO PURPLE)), ((NO REALISM)), ((NO TEXTURE)).
"""

# Анатомия самоката (без сиденья)
SCOOTER_CORE = "OBJECT: A cute miniature Electric Kickboard (scooter). Vertical stem, flat deck. ((NO SEAT))."

# Анатомия машины
CAR_CORE = "OBJECT: A cute miniature White Sedan car with blue stripes."

# Негативный промпт (Мусор)
NEGATIVE_PROMPT = "photo, realistic, 8k, detailed texture, wood, fur, needles, pink, magenta, room, floor, wall, interior, dark, shadow, noise, grain"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 4.0 (Style Fix)", layout="centered", page_icon="🎨")
st.title("🎨 Генератор 4.0: Принудительный стиль")
st.caption("Теперь стиль 'Claymorphism' применяется с двойной силой.")

# Настройки
with st.sidebar:
    use_turbo = st.checkbox("Turbo-режим (быстрее)", value=False)
    model = "turbo" if use_turbo else "flux"

mode = st.radio("Тип объекта:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    # Подсказка пользователю
    user_input = st.text_area("Окружение (например: стоит рядом с елкой)", value="стоит рядом с елкой", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Применяю магию пластика...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. ТРЮК: ПРЕВРАЩАЕМ СЦЕНУ В ИГРУШКУ
        # Вместо "Tree" отправляем "Toy minimal plastic tree"
        toy_scene = f"minimalist plastic toy version of {scene_en}"
        
        # 3. СБОРКА ПРОМПТА
        if "Самокат" in mode:
            # Убираем слово scooter из сцены, чтобы не сбивать анатомию
            safe_scene = toy_scene.replace("scooter", "").replace("bike", "")
            final_prompt = f"{STYLE_HEADER} {SCOOTER_CORE} SCENE: {safe_scene}. {COLOR_RULES} {BACKGROUND_RULE} {STYLE_HEADER}" 
            # ^ Дублируем стиль в конце для надежности
            
        elif "Машина" in mode:
            final_prompt = f"{STYLE_HEADER} {CAR_CORE} SCENE: {toy_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
            
        else:
            final_prompt = f"{STYLE_HEADER} OBJECT: {toy_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
        
        # Добавляем негативный промпт
        final_prompt += f" --no {NEGATIVE_PROMPT}"

        # 4. Отправка
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 99999)
        
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
        
        # Попытка запроса (с ретраем)
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            time.sleep(2)
            response = requests.get(url, timeout=60)

        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            st.success("Готово!")
            st.image(image, caption="Результат", use_container_width=True)
            
            with st.expander("🕵️ Что реально увидела нейросеть?"):
                st.write(final_prompt)
                
            st.download_button("Скачать PNG", image_data, "brand_style.png", "image/png")
        else:
            st.error("Ошибка сервера. Попробуйте еще раз или включите Turbo.")

    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
