import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- СТИЛЬ (ТЯЖЕЛЫЙ ЛЮКС v9) ---
STYLE_PREFIX = """
((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)).
LOOK: Minimalist, Clean geometry, Toy-like but premium.
LIGHTING: Studio softbox, global illumination, no harsh shadows.
"""
STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

# --- ОБЪЕКТЫ ---
OBJECT_CORE = """
OBJECT: A modern Electric Kickboard (Stand-up vehicle).
FORM: Thick vertical tube (Royal Blue), wide flat deck (Snow White).
((NO SEAT)), ((NO SADDLE)). Standing only.
"""
CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# --- ЦВЕТА И ФОН ---
COLOR_RULES = """
PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Wires (#FF9601).
NO PINK. NO PURPLE.
"""
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)). No walls, no floor texture."
NEGATIVE_PROMPT = "photo, realistic, metal, chrome, seat, saddle, motorcycle, scooter, pink, purple, complex background"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 11.0 (Fixed)", layout="centered", page_icon="🛠️")
st.title("🛠️ Генератор 11.0: Исправленный")
st.caption("Исправлена ошибка Python 'unpack NoneType'. Стиль — максимальный.")

mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ (ТЕПЕРЬ БЕЗ БАГОВ) ---
def generate_safe(final_prompt, width, height, seed):
    status_box = st.empty()
    
    # 1. FLUX (Попытка)
    url_flux = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
    status_box.info("💎 Flux: Пробую высокое качество...")
    
    try:
        response = requests.get(url_flux, timeout=25)
        if response.status_code == 200:
            status_box.success("✅ Успех! (Flux)")
            return response.content, "Flux"
    except Exception:
        pass # Молча идем дальше

    # 2. TURBO (Запасной вариант)
    url_turbo = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=turbo&nologo=true&enhance=false&seed={seed}"
    status_box.warning("⚠️ Flux занят. Переключаюсь на Turbo...")
    
    try:
        response = requests.get(url_turbo, timeout=15)
        if response.status_code == 200:
            status_box.success("✅ Готово! (Turbo)")
            return response.content, "Turbo"
        else:
            status_box.error(f"❌ Turbo тоже вернул ошибку: {response.status_code}")
    except Exception as e:
        status_box.error(f"❌ Ошибка соединения: {e}")

    # ВАЖНОЕ ИСПРАВЛЕНИЕ: Всегда возвращаем кортеж, даже при ошибке
    return None, None

# --- ЗАПУСК ---
if submit and user_input:
    try:
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        clean_scene = scene_en.replace("scooter", "").replace("bike", "")
        
        if "Самокат" in mode:
            raw_prompt = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        elif "Машина" in mode:
            raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        else:
            raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
            
        final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        seed = random.randint(1, 99999)

        # Вызов функции
        image_bytes, model_used = generate_safe(final_prompt, width, height, seed)

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            st.image(image, caption=f"Результат ({model_used})", use_container_width=True)
            st.download_button("Скачать PNG", image_bytes, "brand_fixed.png", "image/png")
        else:
            st.error("Не удалось сгенерировать изображение. Попробуйте нажать кнопку еще раз.")

    except Exception as e:
        st.error(f"Ошибка приложения: {e}")

elif submit:
    st.warning("Введите описание.")
