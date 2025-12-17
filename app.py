import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- БРЕНДБУК ---
WORLD_STYLE = """
RENDERING STYLE: 3D Claymorphism. Everything looks like soft matte plastic or Play-Doh. 
TEXTURES: Smooth, clean, no noise. Toy-like proportions.
LIGHTING: Bright studio lighting, soft shadows.
"""

COLOR_RULES = """
STRICT COLOR PALETTE:
1. MAIN BODY: Snow White (Matte Plastic).
2. BRANDING ELEMENTS: Deep Royal Blue.
3. ACCENTS: Vibrant Orange.
4. TIRES: Black.
FORBIDDEN COLORS: NO PINK. NO PURPLE. NO MAGENTA.
"""

SCOOTER_ANATOMY = """
OBJECT: A modern electric KICKBOARD (Standing scooter).
SHAPE: L-shaped silhouette, vertical stem, flat deck. NO SEAT. NO SADDLE.
"""

CAR_ANATOMY = """
OBJECT: A compact carsharing sedan.
LOOK: White body with Blue branding stripes. 
"""

NEGATIVE_PROMPT = "pink, rose, fuchsia, purple, lilac, red, realistic tree, realistic photo, complex details, grunge, noise, seat, saddle, moped"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Generator 3.1 (Stable)", layout="centered", page_icon="🛡️")
st.title("🛡️ Корпоративный Генератор 3.1")
st.caption("Версия с защитой от сбоев сервера и запасной моделью.")

# Боковая панель для настроек стабильности
with st.sidebar:
    st.header("⚙️ Настройки")
    use_turbo = st.checkbox("Использовать Turbo-модель", help="Включите, если 'Ошибка сервера'. Качество чуть ниже, но работает стабильнее.")
    model_name = "turbo" if use_turbo else "flux"

mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина (Каршеринг)", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит под минималистичной пластиковой елкой", height=80)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info(f"Генерация (Модель: {model_name})...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. Сборка промпта
        if "Самокат" in mode:
            safe_scene = scene_en.replace("scooter", "").replace("bike", "")
            final_prompt = f"{WORLD_STYLE} {SCOOTER_ANATOMY} {COLOR_RULES} SCENE: The scooter is {safe_scene}. Everything is made of matte plastic. {NEGATIVE_PROMPT}"
        elif "Машина" in mode:
            final_prompt = f"{WORLD_STYLE} {CAR_ANATOMY} {COLOR_RULES} SCENE: The car is {scene_en}. Everything is made of matte plastic. {NEGATIVE_PROMPT}"
        else:
            final_prompt = f"{WORLD_STYLE} {COLOR_RULES} OBJECT: {scene_en}. {NEGATIVE_PROMPT}"

        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = random.randint(1, 10000)
        
        # Ссылка
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model={model_name}&nologo=true&enhance=false&seed={seed}"
        
        # 3. Умный запрос с повторными попытками
        success = False
        attempts = 0
        max_attempts = 2
        
        while not success and attempts < max_attempts:
            attempts += 1
            try:
                # Увеличенный тайм-аут 90 секунд
                response = requests.get(url, timeout=90)
                
                if response.status_code == 200:
                    image_data = response.content
                    image = Image.open(io.BytesIO(image_data))
                    st.success("Готово!")
                    st.image(image, caption=f"Результат ({mode} | {model_name})", use_container_width=True)
                    
                    st.download_button("⬇️ Скачать PNG", data=image_data, file_name="brand_stable.png", mime="image/png")
                    success = True
                else:
                    st.warning(f"Попытка {attempts}: Сервер вернул ошибку {response.status_code}. Пробую еще раз...")
                    time.sleep(2) # Пауза перед повтором
                    
            except requests.exceptions.Timeout:
                st.warning(f"Попытка {attempts}: Время ожидания истекло. Пробую еще раз...")
            except Exception as e:
                st.error(f"Критическая ошибка: {e}")
                break
        
        if not success:
            st.error("❌ Не удалось получить изображение после нескольких попыток.")
            st.info("Совет: Попробуйте включить галочку 'Использовать Turbo-модель' в меню слева.")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Опишите сцену.")
