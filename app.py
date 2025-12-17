import streamlit as st
import requests
from PIL import Image, ImageOps
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random

# --- ССЫЛКА ПО УМОЛЧАНИЮ (Ninebot Max, ч/б) ---
# Если вы ничего не загрузите, будет использован этот "чистый" самокат такой же формы
DEFAULT_CONTROL_URL = "https://i.imgur.com/1p7qJ7z.png" # Пример силуэта

# --- НАСТРОЙКИ СТИЛЯ ---
GLOBAL_STYLE = """
STYLE: 3D minimalist illustration, claymorphism style, matte plastic texture, smooth rounded shapes, soft studio lighting. High resolution.
COLOR PALETTE: Predominantly Soft Whites (#EAF0F9) and Blue (#0668D7), with Accent Orange (#FF9601) details.
BACKGROUND: Isolated on a COMPLETELY FLAT, SOLID single color background (Soft White). NO shadows, no gradients.
"""

NEGATIVE_PROMPT = "purple, violet, lilac, seat, saddle, vespa, moped, motorcycle, engine, photorealistic, realistic, low quality, text, watermark, shadow on wall, complex background"

st.set_page_config(page_title="Universal 3D Generator", layout="centered", page_icon="🛴")
st.title("🎨 3D Генератор + Ваш Референс")
st.caption("Загрузите картинку самоката, и нейросеть возьмет с неё форму (игнорируя цвет).")

# --- БОКОВАЯ ПАНЕЛЬ ДЛЯ ЗАГРУЗКИ ---
with st.sidebar:
    st.header("1. Загрузка референса")
    uploaded_file = st.file_uploader("Перетащите сюда скриншот самоката", type=["png", "jpg", "jpeg"])
    
    control_url = DEFAULT_CONTROL_URL
    
    if uploaded_file is not None:
        try:
            # 1. Открываем и удаляем цвет (делаем Ч/Б)
            img = Image.open(uploaded_file).convert("L") # L = Grayscale
            st.image(img, caption="Ваш референс (цвет удален)", use_container_width=True)
            
            # 2. Сохраняем в память
            byte_io = io.BytesIO()
            img.save(byte_io, "PNG")
            byte_io.seek(0)
            
            # 3. Трюк: Загружаем на временный хостинг (file.io), чтобы получить URL для нейросети
            # Pollinations нужен публичный URL, он не видит файлы на вашем компьютере.
            with st.spinner("Подготовка референса..."):
                files = {'file': ('ref.png', byte_io, 'image/png')}
                # Используем file.io (хранит файл 14 дней или до 1 скачивания)
                r = requests.post('https://file.io/?expires=1d', files=files)
                if r.status_code == 200:
                    control_url = r.json()['link']
                    st.success("Референс обработан!")
                else:
                    st.error("Не удалось обработать файл. Будет использован стандартный.")
        except Exception as e:
            st.error(f"Ошибка обработки: {e}")

# --- ОСНОВНАЯ ФОРМА ---
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
    st.info("Генерирую...")
    
    try:
        # 1. Перевод
        translator = GoogleTranslator(source='auto', target='en')
        translated_text = translator.translate(user_input)
        
        # 2. Логика (Самокат или нет?)
        is_scooter = "scooter" in translated_text.lower() or "kick" in translated_text.lower()
        
        if is_scooter:
             # Если самокат, меняем слово на kick scooter (чтобы не было мопеда)
            final_text = translated_text.replace("scooter", "kick scooter without seat")
        else:
            final_text = translated_text

        # 3. Сборка промпта
        full_prompt = f"{GLOBAL_STYLE} SCENE DETAILS: {final_text}. {NEGATIVE_PROMPT}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1, 100000)
        
        # 4. Формирование URL
        base_url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        if is_scooter:
            # Используем либо загруженный вами Ч/Б файл, либо стандартный
            final_url = f"{base_url}&image={control_url}&control=0.65" # 0.65 - баланс между формой и креативом
        else:
            final_url = base_url
        
        # 5. Запрос
        response = requests.get(final_url, timeout=60)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption="Результат", use_container_width=True)
            
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
