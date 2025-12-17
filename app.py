import streamlit as st
import google.generativeai as genai
import os
from PIL import Image
import io

# --- НАСТРОЙКА СТИЛЯ (ВАШ БРЕНДБУК) ---
# Мы используем технику "System Prompting", жестко задавая стиль перед запросом пользователя.

STYLE_PREFIX = """
GENERATE AN IMAGE FOLLOWING THESE STRICT BRAND GUIDELINES:

1. VISUAL STYLE:
- 3D minimalist illustration, Claymorphism style.
- Textures: Matte plastic, smooth rounded shapes, soft studio lighting with ambient occlusion.
- Renderer aesthetic: Octane Render, C4D, high fidelity, playful but professional.
- NO noise, NO grunge, NO vintage effects. Clean and modern.

2. COLOR PALETTE (Strict adherence required):
- Primary Colors: Use shades of Blue (#0668D7, #08305E, #0692D7) and Soft Whites/Creams (#EAF0F9, #FFF4EB, #D9E3F1).
- Accent Colors: Bright Blue (#0668D7) and Vibrant Orange (#FF9601).
- Background Colors: STRICTLY FLAT and SOLID. Use ONLY: White, Black, Blue (#0668D7), or Light Grey (#F4F4F4).
- IMPORTANT: The object is 3D, but the background must be 2D, flat, and solid color. NO shadows, NO gradients, NO volume on the background itself.

3. SUBJECTS & PEOPLE:
- People: Minimalist 3D characters, light skin tone, few facial details (stylized).
- Preference: Avoid full figures if possible, focus on hands or objects.
- SCOOTERS (Specific Rule): If electric scooters are present, they must have a battery in the floor deck. NO seats, NO rear-view mirrors, NO logos. Modern shared-mobility style.

4. LIGHTING & COMPOSITION:
- Lighting: Soft, diffused studio light focusing on the object.
- Composition: Clean, plenty of negative space ("air").

5. NEGATIVE PROMPT (DO NOT GENERATE):
- Text, letters, watermarks.
- Complex details, dirt, scratches.
- Scooters with seats or baskets.
- Gradient backgrounds.

USER REQUEST:
"""
# -----------------------------------------------------

st.set_page_config(page_title="3D Brand Generator", layout="centered", page_icon="🛴")

st.title("🛴 Корпоративный 3D Генератор")
st.caption("Создает 3D-иллюстрации в стиле Claymorphism (пластик, минимализм, бренд-цвета).")

# 1. Получаем секретный ключ
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ Не настроен API ключ (GOOGLE_API_KEY).")
    st.stop()

# 2. Настройка модели (Imagen 3 / Nano Banana)
genai.configure(api_key=api_key)
model = genai.GenerativeModel("imagen-3.0-generate-001")

# 3. Форма ввода
with st.form("prompt_form"):
    user_prompt = st.text_area("Что изобразить?", height=100, placeholder="Например: Рука держит смартфон, на экране график роста.")
    
    # Дополнительная настройка соотношения сторон
    aspect_ratio = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Презентация)", "9:16 (Сторис)"], index=0)
    aspect_map = {"1:1 (Квадрат)": "1:1", "16:9 (Презентация)": "16:9", "9:16 (Сторис)": "9:16"}
    
    submit = st.form_submit_button("🎨 Сгенерировать", type="primary")

if submit and user_prompt:
    st.info("Моделирую 3D-сцену... (5-10 сек)")
    
    try:
        # Собираем промпт
        full_prompt = STYLE_PREFIX + user_prompt
        
        # Генерация
        response = model.generate_images(
            prompt=full_prompt,
            number_of_images=1,
            aspect_ratio=aspect_map[aspect_ratio],
            safety_filter_level="block_only_high",
        )

        if response.images:
            image_data = response.images[0]
            img = Image.open(io.BytesIO(image_data.image_bytes))
            
            st.success("Готово!")
            st.image(img, use_column_width=True)
            
            # Скачивание
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="⬇️ Скачать PNG",
                data=byte_im,
                file_name="brand_3d_image.png",
                mime="image/png"
            )
        else:
             st.error("Ошибка генерации. Попробуйте изменить запрос (возможно, сработал фильтр безопасности).")

    except Exception as e:
        st.error(f"Произошла ошибка API: {e}")

elif submit and not user_prompt:
    st.warning("Напишите, что нужно нарисовать.")