import streamlit as st
import requests
import json
import base64
import os
from PIL import Image
import io

# --- НАСТРОЙКИ СТИЛЯ (ВАШ БРЕНДБУК) ---
STYLE_PREFIX = """
GENERATE AN IMAGE FOLLOWING THESE STRICT BRAND GUIDELINES:
1. VISUAL STYLE: 3D minimalist illustration, Claymorphism style. Matte plastic, smooth rounded shapes, soft studio lighting. NO noise, NO grunge.
2. COLOR PALETTE: Blue (#0668D7, #08305E), Soft Whites (#EAF0F9), Accent Orange (#FF9601).
3. BACKGROUND: STRICTLY FLAT and SOLID single color (White, Blue, or Light Grey). NO shadows/gradients on background.
4. SUBJECTS: Minimalist 3D characters, stylized.
5. SCOOTERS: Must have battery in floor deck. NO seats, NO mirrors, NO logos.
6. NEGATIVE PROMPT: Text, letters, watermarks, realistic photos, blurry, complex background.
USER REQUEST:
"""
# -----------------------------------------------------

st.set_page_config(page_title="3D Brand Generator", layout="centered", page_icon="🛴")
st.title("🛴 Корпоративный 3D Генератор (REST API)")

# Получаем ключ
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Не настроен API ключ.")
    st.stop()

with st.form("prompt_form"):
    user_prompt = st.text_area("Что изобразить?", height=100)
    aspect_ratio = st.selectbox("Формат:", ["1:1", "16:9", "9:16"], index=0)
    submit = st.form_submit_button("🎨 Сгенерировать")

if submit and user_prompt:
    st.info("Отправляю запрос в Google... (прямой канал)")
    
    # 1. Формируем URL и заголовки для прямого запроса
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # 2. Формируем тело запроса (JSON)
    full_prompt = STYLE_PREFIX + user_prompt
    payload = {
        "instances": [
            {"prompt": full_prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio
        }
    }

    try:
        # 3. Отправляем запрос
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # 4. Проверяем ошибки
        if response.status_code != 200:
            st.error(f"Ошибка сервера: {response.text}")
        else:
            # 5. Достаем картинку из ответа
            result = response.json()
            # Google отдает картинку в формате Base64, нам нужно её раскодировать
            b64_image = result['predictions'][0]['bytesBase64Encoded']
            image_data = base64.b64decode(b64_image)
            
            img = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(img, use_column_width=True)
            
            # Кнопка скачивания
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="brand_3d_image.png",
                mime="image/png"
            )

    except Exception as e:
        st.error(f"Произошла ошибка соединения: {e}")

elif submit:
    st.warning("Введите описание.")
