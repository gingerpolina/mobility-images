import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
from deep_translator import GoogleTranslator
import random
import time
import os
import datetime
import shutil

# --- ПАПКА ДЛЯ КАРТИНОК ---
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

# --- БРЕНДБУК (LUXURY STYLE) ---
STYLE_PREFIX = """
((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)).
LOOK: Minimalist, Clean geometry, Toy-like but premium.
LIGHTING: Studio softbox, global illumination, no harsh shadows.
"""
STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

OBJECT_CORE = """
OBJECT: A modern Electric Kickboard (Stand-up vehicle).
FORM: Thick vertical tube (Royal Blue), wide flat deck (Snow White).
((NO SEAT)), ((NO SADDLE)). Standing only.
"""
CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Wires (#FF9601). NO PINK."
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)). No walls, no floor texture."
NEGATIVE_PROMPT = "photo, realistic, metal, chrome, seat, saddle, motorcycle, scooter, pink, purple, complex background, text, watermark"

# -----------------------------------------------------

st.set_page_config(page_title="Gen 14.0 (Smart Upscale)", layout="wide", page_icon="✨")
st.title("✨ Генератор 14.0: Быстрый старт + Апскейл")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ ---
def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        # Для 4K даем больше времени (60 сек), для обычного 30
        timeout = 60 if width > 1024 else 30
        response = requests.get(url, timeout=timeout)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

# --- ВКЛАДКИ ---
tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# === 1. ГЕНЕРАТОР ===
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
        aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
        user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=100)
        submit = st.form_submit_button("🚀 Сгенерировать (Быстро)", type="primary")

    with col2:
        if submit and user_input:
            # 1. Готовим промпт
            translator = GoogleTranslator(source='auto', target='en')
            scene_en = translator.translate(user_input)
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            if "Самокат" in mode:
                raw_prompt = f"{STYLE_PREFIX} {OBJECT_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES} SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
                
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 2. Размеры (Базовые 1024)
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 3. Генерация
            with st.spinner("Рисую эскиз..."):
                img_bytes = generate_image(final_prompt, w, h, seed)

            if img_bytes == "BUSY":
                st.warning("Сервер перегружен. Нажмите кнопку еще раз.")
            elif img_bytes:
                # Показываем результат
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, caption=f"Результат ({w}x{h})", use_container_width=True)
                
                # 4. Сохраняем на диск (в имя файла зашиваем параметры)
                # Формат имени: prompthash_seed_width_height.png
                safe_prompt_hash = str(hash(raw_prompt))
                filename = f"img_{seed}_{w}_{h}_{safe_prompt_hash}.png"
                # Но мы сохраним промпт в отдельный текстовый файл для надежности, а имя проще
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                final_filename = f"{timestamp}_{seed}_{w}_{h}.png"
                
                filepath = os.path.join(GALLERY_DIR, final_filename)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                
                # Сохраняем промпт рядом в txt, чтобы потом считать при апскейле
                with open(filepath + ".txt", "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                    
                st.toast("✅ Сохранено в галерею!")
                time.sleep(1)
                st.rerun() # Обновляем страницу, чтобы картинка появилась в галерее

# === 2. ГАЛЕРЕЯ + UPSCALER ===
with tab2:
    # Читаем файлы
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    
    if not files:
        st.info("Галерея пуста.")
    else:
        st.write(f"Всего изображений: {len(files)}")
        
        # Сетка
        cols = st.columns(2)
        
        for i, filename in enumerate(files):
            filepath = os.path.join(GALLERY_DIR, filename)
            txt_path = filepath + ".txt"
            
            # Парсим имя файла: timestamp_seed_width_height.png
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
                width = int(parts[2])
                height = int(parts[3])
                
                # Если ширина > 1500, значит это уже 4K
                is_4k = width > 1500
            except:
                seed = 0
                width = 1024
                is_4k = False

            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        img = Image.open(filepath)
                        st.image(img, use_container_width=True)
                        
                        # Метки
                        if is_4k:
                            st.caption(f"💎 **Ultra HD (4K)** | {width}x{height}")
                        else:
                            st.caption(f"🔹 Standard | {width}x{height}")
                        
                        col_b1, col_b2 = st.columns(2)
                        
                        # Кнопка СКАЧАТЬ
                        with open(filepath, "rb") as f:
                            col_b1.download_button("⬇️ Скачать", f, filename, "image/png", key=f"dl_{filename}")

                        # Кнопка УЛУЧШИТЬ (Только если еще не 4K)
                        if not is_4k:
                            if col_b2.button("✨ Улучшить до 4K", key=f"up_{filename}"):
                                # ЛОГИКА АПСКЕЙЛА
                                if os.path.exists(txt_path):
                                    with open(txt_path, "r", encoding="utf-8") as f:
                                        saved_prompt = f.read()
                                    
                                    with st.spinner("⏳ Генерация 4K (это займет 30-50 сек)..."):
                                        # Удваиваем размер
                                        new_w, new_h = width * 2, height * 2
                                        
                                        # Генерируем
                                        hq_bytes = generate_image(saved_prompt, new_w, new_h, seed)
                                        
                                        if hq_bytes and hq_bytes != "BUSY":
                                            # Перезаписываем старый файл новым (чтобы не плодить дубли)
                                            # Но меняем имя файла, чтобы обновились размеры
                                            new_filename = filename.replace(f"_{width}_{height}", f"_{new_w}_{new_h}")
                                            new_filepath = os.path.join(GALLERY_DIR, new_filename)
                                            
                                            # Сохраняем новую картинку
                                            with open(new_filepath, "wb") as f:
                                                f.write(hq_bytes)
                                            # Копируем файл с промптом к новому имени
                                            shutil.copy(txt_path, new_filepath + ".txt")
                                            
                                            # Удаляем старую (маленькую)
                                            os.remove(filepath)
                                            os.remove(txt_path)
                                            
                                            st.success("Готово! Картинка обновлена.")
                                            st.rerun()
                                        else:
                                            st.error("Не удалось улучшить (сервер занят). Попробуйте позже.")
                                else:
                                    st.error("Не найден файл с промптом.")
