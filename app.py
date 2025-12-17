import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse

# --- НАСТРОЙКИ СТИЛЯ (ВАШ БРЕНДБУК) ---
# Я немного адаптировал промпт под модель Flux/SDXL, чтобы она лучше понимала стиль
STYLE_PREFIX = """
(3D minimalist illustration), (claymorphism style), matte plastic texture, smooth rounded shapes, soft studio lighting, 
clean composition, rendered in Blender, 4k, high resolution.
COLORS: Blue (#0668D7), White, Orange Accent.
BACKGROUND: simple solid color background, flat, no shadows.
OBJECT:
"""

NEGATIVE_PROMPT = "photorealistic, noisy, grunge, text, watermark, low quality, pixelated, complex background, shadow on background"
# -----------------------------------------------------

st.set_page_config(page_title="Free 3D Generator", layout="centered", page_icon="🛴")
st.title("🛴 Бесплатный 3D Генератор (Flux)")
st.caption("Работает на базе Pollinations.ai (No API Key needed)")

with st.form("prompt_form"):
    user_prompt = st.text_area("Что изобразить?", value="Электросамокат стоит под новогодней елкой", height=100)
    
    # Размеры для Pollinations
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("🎨 Сгенерировать бесплатно")

if submit and user_prompt:
    st.info("Генерирую... (обычно занимает 5-10 секунд)")
    
    # 1. Собираем полный промпт
    full_prompt = f"{STYLE_PREFIX} {user_prompt}. {NEGATIVE_PROMPT}"
    
    # 2. Кодируем промпт для URL (превращаем пробелы в %20 и т.д.)
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 3. Формируем ссылку на бесплатный API
    # seed=42 (или случайный) можно добавлять для вариативности
    # model=flux - используем одну из лучших моделей сейчас
    url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=true"
    
    try:
        # 4. Делаем запрос
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Читаем картинку из ответа
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption="Результат (Model: Flux)", use_container_width=True)
            
            # Кнопка скачивания
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="scooter_3d.png",
                mime="image/png"
            )
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            st.write(response.text)
            
    except Exception as e:
        st.error(f"Что-то пошло не так: {e}")

elif submit:
    st.warning("Напишите описание.")
