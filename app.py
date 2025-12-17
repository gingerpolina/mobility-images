import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- НАСТРОЙКИ СТИЛЯ (COMPACT VERSION) ---
# Я немного сократил текст промптов, чтобы URL не был слишком длинным (это тоже причина ошибок)

STYLE_HEADER = "((3D Minimalist Product Render)), ((Matte Soft-Touch Plastic)), ((Unibody Design)), ((Clean Geometry))."
BACKGROUND_RULE = "BACKGROUND: ((PURE WHITE HEX #FFFFFF)), ((Infinite Studio)). No shadows."
COLOR_RULES = "COLORS: Matte Snow White Body, Deep Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601)."

SCOOTER_CORE = """
OBJECT: Modern Electric Kick Scooter.
GEOMETRY: Thick tubular stem, wide flat deck, integrated minimalist fender.
((NO SEAT)), ((NO SADDLE)). Standing only.
"""

CAR_CORE = "OBJECT: Modern autonomous white sedan car, blue branding strip. Minimalist unibody shape."

NEGATIVE_PROMPT = "dashboard, screen, wires, seat, saddle, motorcycle, moped, realistic, dirt, grunge, shadow, pink, purple, red, green"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 8.0 (Auto-Switch)", layout="centered", page_icon="⚡")
st.title("⚡ Генератор 8.0: Авто-переключение")
st.caption("Если Flux (высокое качество) перегружен, я сам переключусь на Turbo.")

mode = st.radio("Тип объекта:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ С ЗАЩИТОЙ ---
def generate_safe(final_prompt, width, height, seed):
    # Попытка 1: FLUX (Высокое качество)
    url_flux = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
    
    status_text = st.empty() # Место для сообщений
    status_text.info("🔄 Попытка 1: Стучимся к Flux (HD качество)...")
    
    try:
        response = requests.get(url_flux, timeout=20) # Ждем 20 сек
        if response.status_code == 200:
            status_text.success("✅ Успех! Сработал Flux.")
            return response.content, "Flux (High Quality)"
    except:
        pass # Если ошибка, молча идем дальше
    
    # Попытка 2: TURBO (Если Flux упал)
    status_text.warning("⚠️ Flux перегружен. Переключаюсь на Turbo (Скорость)...")
    url_turbo = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=turbo&nologo=true&enhance=false&seed={seed}"
    
    try:
        response = requests.get(url_turbo, timeout=15)
        if response.status_code == 200:
            status_text.success("✅ Готово! Использован Turbo.")
            return response.content, "Turbo (Fast Mode)"
    except Exception as e:
        status_text.error(f"❌ Все серверы заняты. Ошибка: {e}")
        return None, None

# --- ОСНОВНАЯ ЛОГИКА ---
if submit and user_input:
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        stylized_scene = f"minimalist composition, {scene_en}, clean forms"
        
        # 2. Сборка (сжатая)
        encoded_scene = urllib.parse.quote(stylized_scene)
        
        if "Самокат" in mode:
            raw_prompt = f"{STYLE_HEADER} {SCOOTER_CORE} {COLOR_RULES} SCENE: {stylized_scene}. {BACKGROUND_RULE}"
        elif "Машина" in mode:
            raw_prompt = f"{STYLE_HEADER} {CAR_CORE} {COLOR_RULES} SCENE: {stylized_scene}. {BACKGROUND_RULE}"
        else:
            raw_prompt = f"{STYLE_HEADER} OBJECT: {stylized_scene}. {COLOR_RULES} {BACKGROUND_RULE}"
            
        final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
        
        # Размеры
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        seed = random.randint(1, 99999)

        # 3. Запуск умной генерации
        image_bytes, model_used = generate_safe(final_prompt, width, height, seed)

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            st.image(image, caption=f"Результат ({model_used})", use_container_width=True)
            st.download_button("Скачать PNG", image_bytes, "brand_gen.png", "image/png")

    except Exception as e:
        st.error(f"Ошибка приложения: {e}")

elif submit:
    st.warning("Введите описание.")
