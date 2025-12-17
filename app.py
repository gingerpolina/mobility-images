import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator

# --- ГЛОБАЛЬНЫЙ СТИЛЬ (ПРИМЕНЯЕТСЯ КО ВСЕМУ) ---
# Описываем только визуальный стиль, цвета и фон. Без конкретного объекта.
GLOBAL_STYLE = """
STYLE: 3D minimalist illustration, claymorphism style, matte plastic texture, smooth rounded shapes, soft studio lighting. High resolution, rendered in Blender.
COLOR PALETTE: Predominantly Soft Whites (#EAF0F9) and Blue (#0668D7), with Accent Orange (#FF9601).
BACKGROUND: Isolated on a COMPLETELY FLAT, SOLID single color background (Soft White). NO shadows on background, no gradients.
"""

# --- СПЕЦИАЛЬНЫЕ ПРАВИЛА ДЛЯ САМОКАТОВ ---
SCOOTER_RULES = """
OBJECT SPECIFICS: Modern electric kick scooter. Must have battery in the floor deck. NO seats. NO mirrors. NO logos. Minimalist design.
"""

NEGATIVE_PROMPT = "photorealistic, realistic, dark, gloomy, low quality, pixelated, text, watermark, complex background, shadow on wall, gradient background"

# -----------------------------------------------------

st.set_page_config(page_title="Universal 3D Generator", layout="centered", page_icon="🎨")
st.title("🎨 Универсальный 3D Генератор (Auto-Translate)")
st.caption("Пишите на русском. Если это самокат — применяются правила бренда.")

with st.form("prompt_form"):
    user_input = st.text_area("Что изобразить?", value="Электросамокат стоит под новогодней елкой", height=100)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Перевожу запрос и генерирую...")
    
    try:
        # 1. АВТОМАТИЧЕСКИЙ ПЕРЕВОД (RU -> EN)
        translator = GoogleTranslator(source='auto', target='en')
        translated_prompt = translator.translate(user_input)
        
        # Показываем пользователю, как перевелось (для контроля)
        st.caption(f"🇬🇧 Перевод для нейросети: *{translated_prompt}*")
        
        # 2. УМНАЯ ЛОГИКА
        # Проверяем, есть ли слово "scooter" в переводе
        final_object_prompt = translated_prompt
        
        if "scooter" in translated_prompt.lower():
            # Если это самокат, добавляем жесткие правила бренда
            full_prompt = f"{GLOBAL_STYLE} {SCOOTER_RULES} SCENE: {translated_prompt}. {NEGATIVE_PROMPT}"
            st.toast("🛴 Обнаружен самокат! Применены правила бренда (без сиденья, батарея в деке).")
        else:
            # Если это что-то другое, просто применяем стиль
            full_prompt = f"{GLOBAL_STYLE} OBJECT: {translated_prompt}. {NEGATIVE_PROMPT}"
        
        # 3. Отправка запроса
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false"
        
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption=f"Результат ({size_option})", use_container_width=True)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="generated_3d.png",
                mime="image/png"
            )
        else:
            st.error("Ошибка на сервере генерации.")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
