import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import os

# --- НАСТРОЙКИ СТИЛЯ (ВАШ БРЕНДБУК) ---
# Я сохранил твой промпт в точности
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
st.title("🛴 Корпоративный 3D Генератор (Imagen 3)")

# Получаем ключ из секретов
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Не найден API ключ! Добавь GOOGLE_API_KEY в секреты Streamlit.")
    st.stop()

# Инициализация клиента (новая библиотека)
client = genai.Client(api_key=api_key)

with st.form("prompt_form"):
    user_prompt = st.text_area("Что изобразить?", height=100)
    aspect_ratio = st.selectbox("Формат:", ["1:1", "16:9", "9:16", "3:4", "4:3"], index=0)
    submit = st.form_submit_button("🎨 Сгенерировать")

if submit and user_prompt:
    st.info("Генерирую изображение через Google GenAI SDK...")
    
    # Склеиваем стиль и запрос пользователя
    full_prompt = STYLE_PREFIX + " " + user_prompt
    
    try:
        # ЗАПРОС ЧЕРЕЗ НОВУЮ БИБЛИОТЕКУ
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=full_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                safety_filter_level="block_only_high"
            )
        )
        
        # Проверяем, пришла ли картинка
        if response.generated_images:
            image = response.generated_images[0].image
            
            st.success("Готово!")
            st.image(image, caption="Результат", use_container_width=True)
            
            # Подготовка для скачивания (конвертируем обратно в байты)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=byte_im,
                file_name="brand_3d_image.png",
                mime="image/png"
            )
        else:
            st.error("Сервер не вернул изображение (пустой ответ).")
            
    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
        st.caption("Совет: Если ошибка '404', попробуйте поменять модель на 'imagen-3.0-generate-002' в коде.")

elif submit:
    st.warning("Пожалуйста, введите описание.")
