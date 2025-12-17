import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random

# --- 1. АНАТОМИЯ САМОКАТА (ЖЕСТКИЙ КАРКАС) ---
# Мы описываем форму словами так, чтобы исключить мопед.
# L-shaped = Г-образная форма. T-bar = Т-образный руль. Flat deck = Плоская дека.
SCOOTER_ANATOMY = """
OBJECT: A modern electric KICK SCOOTER (stand-up type).
SHAPE RULES: The object has a strict L-shaped silhouette.
1. Vertical stem (steering column) with a simple T-bar handlebar at the top.
2. Flat horizontal floorboard (deck) at the bottom for standing.
3. Two small wheels (one front, one back).
4. NO SEAT. NO SADDLE. The user stands on the deck.
"""

# --- 2. СТИЛЬ И ЦВЕТА ---
GLOBAL_STYLE = """
VISUAL STYLE: 3D claymorphism render, matte plastic material, soft rounded edges, friendly studio lighting, minimalism.
COLORS: Main body is White (#EAF0F9) and Blue (#0668D7). Wheels are Black. Small accents are Orange (#FF9601).
BACKGROUND: Isolated on a solid flat Soft White background.
"""

# --- 3. НЕГАТИВНЫЙ ПРОМПТ (ЧТО ЗАПРЕЩЕНО) ---
# Сюда добавил запрет на фиолетовый и усиленный запрет на сиденья
NEGATIVE_PROMPT = """
purple, violet, lilac, pink, 
seat, saddle, chair, bench, 
vespa, moped, scooter with seat, motorcycle, motorbike,
combustion engine, exhaust pipe, 
complex background, realistic photo, noise, grunge, text, watermark
"""

st.set_page_config(page_title="Correct 3D Scooter", layout="centered", page_icon="🛴")
st.title("🛴 Генератор: Правильная форма")
st.caption("Форма самоката жестко описана геометрически (Г-образная рама).")

with st.form("prompt_form"):
    user_input = st.text_area("Детали сцены (где стоит самокат?):", value="стоит рядом с новогодней елкой", height=100)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Генерирую с учетом анатомии...")
    
    try:
        # 1. Перевод запроса пользователя
        translator = GoogleTranslator(source='auto', target='en')
        scene_description = translator.translate(user_input)
        
        # 2. Логика замены слов (на всякий случай чистим ввод пользователя)
        if "scooter" in scene_description.lower():
            scene_description = scene_description.replace("scooter", "kick scooter")

        # 3. СБОРКА ИТОГОВОГО ПРОМПТА
        # Порядок важен: Сначала ЧТО (Анатомия), потом КАК (Стиль), потом ГДЕ (Сцена)
        full_prompt = f"{SCOOTER_ANATOMY} {GLOBAL_STYLE} SCENE CONTEXT: {scene_description}. {NEGATIVE_PROMPT}"
        
        # 4. Кодирование URL
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1, 100000)
        
        # enhance=true иногда добавляет лишние детали (и сиденья), поэтому ставим false
        # но добавляем seed для разнообразия
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        # 5. Запрос
        response = requests.get(url, timeout=45)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            
            # Для отладки можно посмотреть, что мы реально отправили
            with st.expander("Посмотреть текст промпта (Debug)"):
                st.write(full_prompt)
                
            st.image(image, caption="Результат", use_container_width=True)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="scooter_fixed.png",
                mime="image/png"
            )
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
