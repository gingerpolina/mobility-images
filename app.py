import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time

# --- НАСТРОЙКИ 9.0 (ВОЗВРАТ К ДЕТАЛЯМ) ---

# 1. СТИЛЬ: Максимально подробный, чтобы перебить реализм.
STYLE_PREFIX = """
((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)).
LOOK: Minimalist, Clean geometry, Toy-like but premium.
LIGHTING: Studio softbox, global illumination, no harsh shadows.
"""

STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

# 2. АНАТОМИЯ: Используем слово KICKBOARD вместо Scooter.
# Это "хак", чтобы Flux перестал рисовать мопеды.
OBJECT_CORE = """
OBJECT: A modern Electric Kickboard (Stand-up vehicle).
FORM: 
1. A thick vertical tube (steering stem) in Royal Blue.
2. A wide flat board (deck) in Snow White.
3. Two small wheels.
4. ((NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). Standing only.
"""

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# 3. ЦВЕТА
COLOR_RULES = """
PALETTE:
- DECK/BODY: Matte Snow White (#EAF0F9).
- STEM/STRIPES: Deep Royal Blue (#0668D7).
- WIRES/BRAKES: Neon Orange (#FF9601).
- TIRES: Black Rubber.
NO PINK. NO PURPLE. NO REALISM.
"""

# 4. ФОН
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)), ((Infinite Studio)). No walls, no floor texture."

# 5. НЕГАТИВ (Запреты)
NEGATIVE_PROMPT = "photo, realistic, photography, metal, chrome, reflection, dirt, shadow, seat, saddle, motorcycle, scooter, moped, pink, purple, complex background"

# -----------------------------------------------------

st.set_page_config(page_title="Brand Gen 9.0 (Strict)", layout="centered", page_icon="💎")
st.title("💎 Генератор 9.0: Строгий Стиль")
st.caption("Вернулись к сложным промптам. Кикборд вместо Самоката (чтобы без сиденья).")

mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"], horizontal=True)

with st.form("prompt_form"):
    user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=80)
    size_option = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("✨ Сгенерировать")

# Функция повторных попыток
def generate_with_retry(url, retries=2):
    for i in range(retries + 1):
        try:
            # Увеличенный тайм-аут для Flux (он медленный, но качественный)
            response = requests.get(url, timeout=45)
            if response.status_code == 200:
                return response.content
        except requests.exceptions.RequestException:
            time.sleep(2) # Пауза перед повтором
    return None

if submit and user_input:
    st.info("Генерация (Flux)...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        scene_en = translator.translate(user_input)
        
        # 2. Сборка "Сэндвича"
        # Стиль + Анатомия + Цвета + Сцена + Фон + Стиль(еще раз)
        
        # Очищаем сцену от вредных слов
        clean_scene = scene_en.replace("scooter", "").replace("bike", "").replace("moped", "")
        
        if "Самокат" in mode:
            raw_prompt = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        elif "Машина" in mode:
            raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
        else:
            raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
            
        # Добавляем негативный промпт
        final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
        
        # 3. URL
        width, height = (1024, 1024) if size_option == "1:1" else ((1280, 720) if "16:9" in size_option else (720, 1280))
        seed = random.randint(1, 99999)
        
        # Используем ТОЛЬКО Flux, так как Turbo не понимает стиль. 
        # enhance=false - чтобы не добавлял отсебятину.
        url = f"https://pollinations.ai/p/{final_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        # 4. Запрос
        image_bytes = generate_with_retry(url)

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            st.success("Готово!")
            st.image(image, caption="Результат (Flux Strict)", use_container_width=True)
            
            with st.expander("Посмотреть полный запрос"):
                st.write(raw_prompt)
                
            st.download_button("Скачать PNG", image_bytes, "brand_v9.png", "image/png")
        else:
            st.error("Ошибка сервера: Flux перегружен. Попробуйте через минуту.")

    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
