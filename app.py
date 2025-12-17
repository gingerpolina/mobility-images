import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random

# --- БИБЛИОТЕКА ПРОМПТОВ (БРЕНДБУК) ---

# 1. ОБЩИЙ СТИЛЬ (Работает всегда)
BASE_STYLE = """
STYLE: 3D cute minimalist render, claymorphism, matte plastic texture, smooth rounded shapes, bright studio lighting. High resolution.
COLORS: The object is primarily MATTE WHITE (#EAF0F9). Major details are BLUE (#0668D7). Tiny accents are ORANGE (#FF9601).
BACKGROUND: Isolated on a SOLID WHITE background. NO gradients. NO shadows on wall.
"""

# 2. НАСТРОЙКИ ДЛЯ САМОКАТА (Убиваем сиденья)
# Трюк: используем слово Kickboard вместо Scooter, чтобы не было мопедов.
SCOOTER_PROMPT = """
OBJECT: A modern electric KICKBOARD (stand-up kick scooter).
ANATOMY: 
1. A flat horizontal deck (floorboard) for standing.
2. A vertical stem connected to the front of the deck.
3. A simple T-bar handlebar.
4. Two small wheels.
STRICT RULES: NO SEAT. NO SADDLE. NO CHAIR. It is for standing only.
"""

# 3. НАСТРОЙКИ ДЛЯ КАРШЕРИНГА
CAR_PROMPT = """
OBJECT: A modern carsharing vehicle (compact sedan).
APPEARANCE: The car body is MATTE WHITE. There is a BLUE branding strip on the side door. 
DETAILS: Smooth minimalist wheels, black windows. Friendly 3D shape.
"""

# 4. НЕГАТИВНЫЙ ПРОМПТ (Мусор)
NEGATIVE_PROMPT = "purple, pink, violet, lilac, red, green body, grunge, noise, pixelated, text, logo, watermark, realistic photo, dark, shadow, complex background"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Generator 2.0", layout="centered", page_icon="🎨")
st.title("🎨 Корпоративный Генератор 2.0")
st.caption("Выберите тип объекта, чтобы применить правильные правила формы.")

# --- ВЫБОР РЕЖИМА ---
mode = st.radio(
    "Что генерируем?",
    ["🛴 Самокат (Urent)", "🚗 Машина (Каршеринг)", "📦 Другой объект (Общий стиль)"],
    horizontal=True
)

with st.form("prompt_form"):
    user_input = st.text_area("Детали сцены (например: стоит под елкой)", height=80)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Обработка запроса...")
    
    try:
        # 1. Перевод ввода пользователя
        translator = GoogleTranslator(source='auto', target='en')
        scene_details = translator.translate(user_input)
        
        # 2. Выбор правильного "каркаса"
        if "Самокат" in mode:
            # Если выбран самокат - берем жесткую анатомию самоката + сцену
            # И удаляем слово "scooter" из ввода пользователя, чтобы не сбить модель
            clean_scene = scene_details.replace("scooter", "").replace("bike", "")
            final_prompt = f"{SCOOTER_PROMPT} {BASE_STYLE} SCENE: {clean_scene}. {NEGATIVE_PROMPT}"
            
        elif "Машина" in mode:
            # Если машина - берем каркас машины
            final_prompt = f"{CAR_PROMPT} {BASE_STYLE} SCENE: {scene_details}. {NEGATIVE_PROMPT}"
            
        else:
            # Общий режим - просто стиль + то, что написал пользователь
            final_prompt = f"{BASE_STYLE} OBJECT: {scene_details}. {NEGATIVE_PROMPT}"

        # 3. Кодирование URL
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 10000)
        
        # enhance=false важно, чтобы он не додумывал "красивые" детали типа фиолетового неба
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        # 4. Запрос
        response = requests.get(url, timeout=45)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption=f"Результат ({mode})", use_container_width=True)
            
            with st.expander("🛠 Проверить отправленный промпт"):
                st.write(final_prompt)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="brand_gen_2.png",
                mime="image/png"
            )
        else:
            st.error("Ошибка сервера Pollinations.")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
