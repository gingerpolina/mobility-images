import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- БЛОК СТИЛЯ (ВЕРСИЯ 9.0 - ТЯЖЕЛЫЙ ЛЮКС) ---
# Мы сохраняем эти настройки, потому что они давали лучший визуальный результат.

STYLE_PREFIX = """
((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)).
LOOK: Minimalist, Clean geometry, Toy-like but premium.
LIGHTING: Studio softbox, global illumination, no harsh shadows.
"""

STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

# Используем KICKBOARD, чтобы не было сиденья
OBJECT_CORE = """
OBJECT: A modern Electric Kickboard (Stand-up vehicle).
FORM: 
1. A thick vertical tube (steering stem) in Royal Blue.
2. A wide flat board (deck) in Snow White.
3. Two small wheels.
4. ((NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). Standing only.
"""

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

COLOR_RULES = """
PALETTE:
- DECK/BODY: Matte Snow White (#EAF0F9).
- STEM/STRIPES: Deep Royal Blue (#0668D7).
- WIRES/BRAKES: Neon Orange (#FF9601).
- TIRES: Black Rubber.
NO PINK. NO PURPLE. NO REALISM.
"""

BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)), ((Infinite Studio)). No walls, no floor texture."

NEGATIVE_PROMPT = "photo, realistic, photography, metal, chrome, reflection, dirt, shadow, seat, saddle, motorcycle, scooter, moped, pink, purple, complex background"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 10.0 (Hybrid)", layout="centered", page_icon="🛡️")
st.title("🛡️ Генератор 10.0: Гибрид")
st.caption("Стиль из Версии 9 + Надежность из Версии 8. Если Flux занят, сработает Turbo.")

mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

# --- ФУНКЦИЯ "НЕПРОБИВАЕМОСТИ" ---
def generate_safe(final_prompt, width, height, seed):
    # 1. Сначала пробуем FLUX (Лучшее качество)
    url_flux = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
    
    status_box = st.empty() # Место для сообщений
    status_box.info("💎 Попытка 1: Стучимся к Flux (HD качество)...")
    
    try:
        # Ждем 25 секунд. Если Flux жив, он ответит.
        response = requests.get(url_flux, timeout=25)
        if response.status_code == 200:
            status_box.success("✅ Успех! Сработал Flux.")
            return response.content, "Flux (High Quality)"
    except:
        pass # Если ошибка тайм-аута или соединения — не падаем, а идем дальше
    
    # 2. Если Flux молчит -> ПЕРЕКЛЮЧАЕМСЯ НА TURBO (Спасательный круг)
    status_box.warning("⚠️ Flux перегружен. Включаю Turbo (Быстрый режим)...")
    
    # Turbo модель (она очень быстрая и почти никогда не падает)
    url_turbo = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=turbo&nologo=true&enhance=false&seed={seed}"
    
    try:
        response = requests.get(url_turbo, timeout=15)
        if response.status_code == 200:
            status_box.success("✅ Готово! Использован Turbo.")
            return response.content, "Turbo (Backup Mode)"
    except Exception as e:
        status_box.error(f"❌ Полный отказ серверов. Ошибка: {e}")
        return None, None

# --- ОСНОВНАЯ ЛОГИКА ---
if submit and user_input:
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. Сборка промпта (Жесткий стиль)
        clean_scene = scene_en.replace("scooter", "").replace("bike", "").replace("moped", "")
        
        if "Самокат" in mode:
            raw_prompt = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        elif "Машина" in mode:
            raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        else:
            raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
            
        final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
        
        # 3. Размеры и Seed
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        seed = random.randint(1, 99999)

        # 4. ЗАПУСК
        image_bytes, model_used = generate_safe(final_prompt, width, height, seed)

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            st.image(image, caption=f"Результат ({model_used})", use_container_width=True)
            
            with st.expander("Посмотреть промпт"):
                st.write(raw_prompt)

            st.download_button("Скачать PNG", image_bytes, "brand_safe.png", "image/png")

    except Exception as e:
        st.error(f"Ошибка приложения: {e}")

elif submit:
    st.warning("Введите описание.")
