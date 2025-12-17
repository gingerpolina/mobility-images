import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse

# --- НОВЫЕ ЖЕСТКИЕ НАСТРОЙКИ СТИЛЯ (ДЛЯ FLUX) ---
# Мы сразу говорим модели, ЧТО рисовать (самокат) и В КАКОМ СТИЛЕ.
# Ваш запрос на русском будет добавляться в конец этого блока.
GLOBAL_PROMPT = """
A clean 3D minimalist render of a modern electric kick scooter.
STYLE: Claymorphism, matte plastic texture, smooth rounded shapes, soft friendly studio lighting. No grunge, no noise.
COLOR PALETTE: The scooter is predominantly Soft White (#EAF0F9) and Blue (#0668D7), with distinct Orange (#FF9601) accents on wheels/controls.
BACKGROUND: The object stands isolated against a COMPLETELY FLAT, SOLID single color background (Soft White #EAF0F9). THERE ARE NO CAST SHADOWS on the floor or background. Zero gradients.
SCENE DETAILS: The scooter is
"""

# Усилили негативный промпт против теней и реализма
NEGATIVE_PROMPT = "photorealistic, realistic, cast shadows, floor shadows, ambient occlusion, complex background, indoors, outdoors, detailed environment, grunge, text, watermark"
# -----------------------------------------------------

st.set_page_config(page_title="Free 3D Generator", layout="centered", page_icon="🛴")
st.title("🛴 Бесплатный 3D Генератор (Flux v2)")
st.caption("Работает на базе Pollinations.ai. Стиль и объект закреплены жестко.")

with st.form("prompt_form"):
    # Теперь пользователь добавляет только детали сцены
    user_prompt = st.text_area("Детали сцены (например: стоит рядом с новогодней елкой):", value="стоит рядом с минималистичной новогодней елкой", height=100)
    
    size_option = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"], index=0)
    
    if size_option == "1:1 (Квадрат)":
        width, height = 1024, 1024
    elif size_option == "16:9 (Широкий)":
        width, height = 1280, 720
    else:
        width, height = 720, 1280
        
    submit = st.form_submit_button("🎨 Сгенерировать бесплатно")

if submit and user_prompt:
    st.info("Генерирую... (Модель Flux, 5-15 секунд)")
    
    # 1. Собираем полный промпт: Жесткая база + ваш запрос + негативный промпт
    # Мы добавляем ваш текст после "The scooter is..."
    full_prompt = f"{GLOBAL_PROMPT} {user_prompt}. {NEGATIVE_PROMPT}"
    
    # 2. Кодируем для URL
    encoded_prompt = urllib.parse.quote(full_prompt)
    
    # 3. Ссылка на API Pollinations
    # Добавил enhance=false, чтобы сервис меньше "фантазировал" от себя
    url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false"
    
    try:
        response = requests.get(url, timeout=45)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            # Показываем, какой именно промпт улетел в модель (для отладки)
            with st.expander("Посмотреть полный отправленный промпт"):
                st.write(full_prompt)
            st.image(image, caption="Результат (Flux)", use_container_width=True)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="scooter_3d_flux.png",
                mime="image/png"
            )
        else:
            st.error(f"Ошибка сервера Pollinations: {response.status_code}")
            st.write("Попробуйте еще раз через минуту.")
            
    except Exception as e:
        st.error(f"Ошибка соединения: {e}")

elif submit:
    st.warning("Напишите детали сцены.")
