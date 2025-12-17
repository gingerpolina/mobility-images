import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random

# --- ЖЕСТКИЙ РЕФЕРЕНС (СИЛУЭТ САМОКАТА) ---
# Это ссылка на черно-белый контур правильного самоката.
# Нейросеть будет использовать его как трафарет.
CONTROL_IMAGE_URL = "https://i.imgur.com/Lm3Yc5E.png"

# --- НАСТРОЙКИ СТИЛЯ ---
GLOBAL_STYLE = """
STYLE: 3D minimalist illustration, claymorphism style, matte plastic texture, smooth rounded shapes, soft studio lighting. High resolution.
COLOR PALETTE: Predominantly Soft Whites (#EAF0F9) and Blue (#0668D7), with Accent Orange (#FF9601) details.
BACKGROUND: Isolated on a COMPLETELY FLAT, SOLID single color background (Soft White). NO shadows, no gradients.
"""

NEGATIVE_PROMPT = "seat, saddle, vespa, moped, motorcycle, engine, photorealistic, realistic, low quality, text, watermark, shadow on wall, complex background"

st.set_page_config(page_title="Universal 3D Generator", layout="centered", page_icon="🛴")
st.title("🎨 3D Генератор + Референс формы")
st.caption("Теперь с жестким контролем формы самоката через картинку-образец.")

with st.form("prompt_form"):
    user_input = st.text_area("Что изобразить?", value="Электросамокат стоит рядом с новогодней елкой с подарками", height=100)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("✨ Сгенерировать")

if submit and user_input:
    st.info("Обрабатываю запрос...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        translated_text = translator.translate(user_input)
        
        # 2. Логика референса
        is_scooter = "scooter" in translated_text.lower()
        
        if is_scooter:
            st.toast("🛴 Применяю жесткий трафарет формы самоката (ControlNet).")
            # Уточняем текст, хотя главную роль сыграет картинка
            final_text = translated_text.replace("scooter", "kick scooter without seat")
        else:
            final_text = translated_text

        # 3. Сборка промпта
        full_prompt = f"{GLOBAL_STYLE} SCENE DETAILS: {final_text}. {NEGATIVE_PROMPT}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1, 100000)
        
        # 4. Формирование URL (САМОЕ ВАЖНОЕ)
        base_url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        # Если это самокат, добавляем параметр image с нашим силуэтом
        if is_scooter:
            # control=0.8 означает, что нейросеть должна на 80% придерживаться формы на картинке
            final_url = f"{base_url}&image={CONTROL_IMAGE_URL}&control=0.8"
            # Показываем референс для понимания
            with st.expander("Посмотреть используемый трафарет"):
                st.image(CONTROL_IMAGE_URL, width=200)
        else:
            final_url = base_url
        
        # 5. Запрос
        response = requests.get(final_url, timeout=60)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption=f"Результат ({size_option})", use_container_width=True)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="generated_3d_ref.png",
                mime="image/png"
            )
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
