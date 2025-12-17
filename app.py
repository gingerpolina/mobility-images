import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random

# --- БРЕНДБУК: ЦВЕТА И СТИЛЬ ---

# 1. ГЛОБАЛЬНЫЙ СТИЛЬ (ПРИМЕНЯЕТСЯ КО ВСЕМУ ИЗОБРАЖЕНИЮ)
# Мы говорим: "Весь мир сделан из мягкого пластика". Это исправит реалистичную елку.
WORLD_STYLE = """
RENDERING STYLE: 3D Claymorphism. Everything looks like soft matte plastic or Play-Doh. 
TEXTURES: Smooth, clean, no noise. Toy-like proportions.
LIGHTING: Bright studio lighting, soft shadows.
"""

# 2. ЦВЕТОВАЯ ПАЛИТРА (ПЕРЕВОД HEX В СЛОВА)
# Нейросети плохо понимают HEX (#0668D7), им нужны названия.
# #0668D7 -> Royal Blue / Corporate Blue
# #EAF0F9 -> Snow White / Soft Grey
# #FF9601 -> Vibrant Safety Orange
COLOR_RULES = """
STRICT COLOR PALETTE:
1. MAIN BODY: Snow White (Matte Plastic).
2. BRANDING ELEMENTS: Deep Royal Blue.
3. ACCENTS (Wires/Brakes): Vibrant Orange.
4. TIRES: Black.
FORBIDDEN COLORS: NO PINK. NO PURPLE. NO MAGENTA. NO PASTEL COLORS.
"""

# 3. АНАТОМИЯ САМОКАТА (БЕЗ СИДЕНЬЯ)
SCOOTER_ANATOMY = """
OBJECT: A modern electric KICKBOARD (Standing scooter).
SHAPE:
- L-shaped silhouette.
- Vertical steering stem.
- Flat deck for standing.
- NO SEAT. NO SADDLE.
"""

# 4. АНАТОМИЯ МАШИНЫ
CAR_ANATOMY = """
OBJECT: A compact carsharing sedan.
LOOK: White body with Blue branding stripes on the side. 
"""

# 5. МУСОР (НЕГАТИВНЫЙ ПРОМПТ)
NEGATIVE_PROMPT = "pink, rose, fuchsia, purple, lilac, red, realistic tree, realistic photo, organic texture, bark, fur, complex details, grunge, noise, seat, saddle, moped"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Generator 3.0", layout="centered", page_icon="🎨")
st.title("🛴 Корпоративный Генератор 3.0")
st.caption("Исправлены цвета (нет розовому!) и стиль окружения (елка теперь тоже 3D).")

# Переключатель
mode = st.radio(
    "Тип объекта:",
    ["🛴 Самокат (Urent)", "🚗 Машина (Каршеринг)", "📦 Другое"],
    horizontal=True
)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение (например: стоит под елкой)", value="стоит под минималистичной пластиковой елкой", height=80)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Генерация с коррекцией цвета и стиля...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. Сборка промпта
        # Мы "обволакиваем" ваш запрос стилем со всех сторон
        
        if "Самокат" in mode:
            # Убираем опасные слова из ввода пользователя
            safe_scene = scene_en.replace("scooter", "").replace("bike", "")
            # Промпт: Стиль Мира + Анатомия + Цвета + Сцена + "сделано из пластика"
            final_prompt = f"{WORLD_STYLE} {SCOOTER_ANATOMY} {COLOR_RULES} SCENE: The scooter is {safe_scene}. Everything is made of matte plastic. {NEGATIVE_PROMPT}"
            
        elif "Машина" in mode:
            final_prompt = f"{WORLD_STYLE} {CAR_ANATOMY} {COLOR_RULES} SCENE: The car is {scene_en}. Everything is made of matte plastic. {NEGATIVE_PROMPT}"
            
        else:
            final_prompt = f"{WORLD_STYLE} {COLOR_RULES} OBJECT: {scene_en}. {NEGATIVE_PROMPT}"

        # 3. Отправка
        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 10000)
        
        # flux-pro или flux-realism иногда лучше слушают цвета
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        response = requests.get(url, timeout=45)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption=f"Результат ({mode})", use_container_width=True)
            
            with st.expander("🔍 Что мы отправили нейросети (Debug)"):
                st.write(final_prompt)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="brand_v3.png",
                mime="image/png"
            )
        else:
            st.error("Ошибка сервера.")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Опишите сцену.")
