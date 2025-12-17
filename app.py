import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ СТИЛЯ ---
GLOBAL_STYLE = """
STYLE: 3D minimalist illustration, claymorphism style, matte plastic texture, smooth rounded shapes, soft studio lighting. High resolution, rendered in Blender.
COLOR PALETTE: Predominantly Soft Whites (#EAF0F9) and Blue (#0668D7), with Accent Orange (#FF9601).
BACKGROUND: Isolated on a COMPLETELY FLAT, SOLID single color background (Soft White). NO shadows on background, no gradients.
"""

# Жесткий негативный промпт: запрещаем мопеды и сиденья
NEGATIVE_PROMPT = "seat, saddle, vespa, moped, motorcycle, engine, exhaust, photorealistic, realistic, dark, gloomy, low quality, pixelated, text, watermark, complex background, shadow on wall"

st.set_page_config(page_title="Universal 3D Generator", layout="centered", page_icon="🛴")
st.title("🎨 Универсальный 3D Генератор (Smart Fix)")
st.caption("Исправлена проблема 'скутер вместо самоката'. Пишите на русском.")

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
    st.info("Перевожу и корректирую запрос...")
    
    try:
        # 1. ПЕРЕВОД (RU -> EN)
        translator = GoogleTranslator(source='auto', target='en')
        translated_text = translator.translate(user_input)
        
        # 2. УМНАЯ КОРРЕКЦИЯ ТЕРМИНОВ
        # Если пользователь написал "самокат" (scooter), мы уточняем, что это НЕ мопед.
        # Мы заменяем "scooter" на "stand-up kick scooter" (стоячий самокат)
        
        final_text = translated_text
        
        if "scooter" in translated_text.lower():
            final_text = translated_text.replace("scooter", "modern stand-up electric kick scooter")
            final_text = final_text.replace("electric electric", "electric") # убираем возможные повторы
            
            st.toast("🔧 Исправлено: 'Scooter' заменено на 'Kick Scooter' (без сиденья).")
        
        st.caption(f"🇬🇧 Итоговый запрос к нейросети: *{final_text}*")

        # 3. СБОРКА ПРОМПТА
        # Важно: Сначала стиль, потом ВАШ текст (с елкой), потом негативный промпт.
        full_prompt = f"{GLOBAL_STYLE} SCENE: {final_text}. Make sure the scooter has NO SEAT. {NEGATIVE_PROMPT}"
        
        # 4. ОТПРАВКА
        encoded_prompt = urllib.parse.quote(full_prompt)
        # seed случайный, чтобы картинки были разными каждый раз
        import random
        seed = random.randint(1, 10000)
        
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true&enhance=false&seed={seed}"
        
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            
            st.success("Готово!")
            st.image(image, caption=f"Результат ({size_option})", use_container_width=True)
            
            st.download_button(
                label="⬇️ Скачать PNG",
                data=image_data,
                file_name="fixed_scooter.png",
                mime="image/png"
            )
        else:
            st.error("Ошибка на сервере генерации.")
            
    except Exception as e:
        st.error(f"Ошибка: {e}")

elif submit:
    st.warning("Введите описание.")
