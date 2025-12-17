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

# ==========================================
# 1. НАСТРОЙКИ И ИНИЦИАЛИЗАЦИЯ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v16 (Fixes)", layout="wide", page_icon="🛠️")
st.title("🛠️ Urent Gen v16: Работа над ошибками")

# ==========================================
# 2. БРЕНДБУК (АГРЕССИВНЫЙ ПЛАСТИК)
# ==========================================

# ИЗМЕНЕНИЕ 1: Более жесткий стиль в начале.
# Используем двойные скобки для усиления внимания нейросети.
STYLE_PREFIX = (
    "((NO REALISM)). ((3D Clay Render)), ((Matte Plastic Toy World)). "
    "STYLE: Minimalist, smooth rounded shapes, clean geometry, Play-Doh texture. "
    "MATERIAL: Soft-touch matte plastic everywhere. "
    "LIGHTING: Bright studio setup, soft blurry shadows. "
)

# ИЗМЕНЕНИЕ 2: Уточнение в конце.
STYLE_SUFFIX = "The entire scene is made of clean matte plastic pieces. Isometric view. Blender 3D."

# Анатомия (без изменений, она хорошая)
SCOOTER_CORE = (
    "OBJECT: A modern Electric Kickboard (Stand-up vehicle). "
    "FORM: Thick vertical tube (Royal Blue), wide flat deck (Snow White). "
    "((NO SEAT)), ((NO SADDLE)). Standing only."
)
CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# Цвета
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Wires (#FF9601). NO PINK."
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)). No walls, no floor texture, isolated."

# ИЗМЕНЕНИЕ 3: Усиленный негативный промпт против реализма.
NEGATIVE_PROMPT = "realistic, photo, photography, grain, noise, highly detailed, texture, metal, reflection, shiny, complex, dirt, grunge, seat, saddle, pink, purple, watermark, text"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    # Формируем URL
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    
    try:
        # Увеличенный тайм-аут для попыток 4K
        timeout_val = 90 if width > 1500 else 30
        response = requests.get(url, timeout=timeout_val)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

# ==========================================
# 4. ИНТЕРФЕЙС
# ==========================================

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея и Апскейл"])

# --- ВКЛАДКА 1: ГЕНЕРАТОР ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("generation_form"):
            st.header("Настройки")
            mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Окружение (например: стоит рядом с елкой):", height=100)
            submitted = st.form_submit_button("🚀 Сгенерировать (Базовое качество)", type="primary")

    with col2:
        if submitted and user_input:
            # 1. Перевод
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input)
            except:
                scene_en = user_input
            
            # Превращаем ввод пользователя в "игрушечную версию"
            clean_scene = f"minimalist plastic toy version of {scene_en}".replace("scooter", "").replace("bike", "")
            
            # 2. Сборка промпта
            if "Самокат" in mode:
                part1 = f"{STYLE_PREFIX} {SCOOTER_CORE} {COLOR_RULES}"
                part2 = f"SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
            elif "Машина" in mode:
                part1 = f"{STYLE_PREFIX} {CAR_CORE} {COLOR_RULES}"
                part2 = f"SCENE: {clean_scene}. {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
            else:
                part1 = f"{STYLE_PREFIX} OBJECT: {clean_scene}."
                part2 = f"{COLOR_RULES} {BACKGROUND} {STYLE_SUFFIX}"
                raw_prompt = part1 + " " + part2
                
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 3. Размеры (Базовые)
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s * 1.2), int(base_s * 0.6)
            elif "9:16" in aspect: w, h = int(base_s * 0.6), int(base_s * 1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 4. Генерация
            with st.spinner("Генерация базовой версии..."):
                img_bytes = generate_image(final_prompt, w, h, seed)

            if img_bytes == "BUSY":
                st.warning("Сервер перегружен. Попробуйте через 10 секунд.")
            elif img_bytes:
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, caption=f"Результат ({w}x{h})", use_container_width=True)
                
                # Сохранение
                t_str = datetime.datetime.now().strftime("%H%M%S")
                final_filename = f"{t_str}_{seed}_{w}_{h}.png"
                filepath = os.path.join(GALLERY_DIR, final_filename)
                
                with open(filepath, "wb") as f: f.write(img_bytes)
                with open(filepath + ".txt", "w", encoding="utf-8") as f: f.write(final_prompt)
                    
                st.toast("✅ Сохранено в галерею! Теперь можно улучшить до 4K.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Ошибка соединения.")

# --- ВКЛАДКА 2: ГАЛЕРЕЯ ---
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    
    if not files:
        st.info("В галерее пусто.")
    else:
        st.write(f"Сохранено работ: {len(files)}")
        cols = st.columns(2)
        
        for i, filename in enumerate(files):
            filepath = os.path.join(GALLERY_DIR, filename)
            txt_path = filepath + ".txt"
            
            # Парсим имя
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
                width = int(parts[2])
                height = int(parts[3])
                is_4k = width > 1500 # Метка, что мы ДУМАЕМ, что это 4K
            except:
                seed=0; width=1024; height=1024; is_4k=False

            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        # --- ВАЖНО: ПРОВЕРКА РЕАЛЬНОГО РАЗМЕРА ---
                        img = Image.open(filepath)
                        real_w, real_h = img.size # Читаем реальные пиксели
                        st.image(img, use_container_width=True)
                    except:
                        st.error("Ошибка чтения файла")
                        continue

                    # Метки качества (на основе РЕАЛЬНЫХ данных)
                    # Если реальная ширина > 1800 - считаем это честным 4K
                    if real_w > 1800:
                        st.caption(f"💎 **Ultra HD (Честные 4K)** | Реальный размер: {real_w}x{real_h}")
                        can_upscale = False
                    else:
                        st.caption(f"🔹 Standard | Реальный размер: {real_w}x{real_h}")
                        can_upscale = True
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    # 1. СКАЧАТЬ
                    with open(filepath, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"dl_{filename}")

                    # 2. УЛУЧШИТЬ (АПСКЕЙЛ)
                    if can_upscale:
                        if c2.button("✨ В 4K", key=f"up_{filename}", help="Попытаться получить 2048x2048"):
                            if os.path.exists(txt_path):
                                with open(txt_path, "r", encoding="utf-8") as f: saved_prompt = f.read()
                                
                                with st.spinner("⏳ Попытка генерации 4K (может занять минуту)..."):
                                    # Запрашиваем 2048x2048
                                    target_w, target_h = 2048, 2048
                                    hq_bytes = generate_image(saved_prompt, target_w, target_h, seed)
                                    
                                    if hq_bytes and hq_bytes != "BUSY":
                                        # --- ИЗМЕНЕНИЕ 4: ТАМОЖЕННЫЙ КОНТРОЛЬ ---
                                        # Прежде чем сохранять, проверяем, что нам прислали.
                                        temp_img = Image.open(io.BytesIO(hq_bytes))
                                        received_w, received_h = temp_img.size
                                        
                                        if received_w < 1800:
                                            # Сервер обманул нас и прислал маленькую картинку
                                            st.warning(f"⚠️ Сервер перегружен и не смог выдать 4K. Он прислал только {received_w}x{received_h}. Попробуйте позже.")
                                        else:
                                            # Успех! Это реально большая картинка. Сохраняем.
                                            new_name = filename.replace(f"_{width}_{height}", f"_{received_w}_{received_h}")
                                            new_path = os.path.join(GALLERY_DIR, new_name)
                                            
                                            with open(new_path, "wb") as f: f.write(hq_bytes)
                                            shutil.copy(txt_path, new_path + ".txt")
                                            
                                            os.remove(filepath) # Удаляем старую
                                            os.remove(txt_path)
                                            st.success("Успешно улучшено до 4K!")
                                            time.sleep(1)
                                            st.rerun()
                                    else:
                                        st.error("Сервер занят (тайм-аут или 429).")
                            else:
                                st.error("Промпт потерян.")

                    # 3. УДАЛИТЬ
                    if c3.button("🗑️", key=f"del_{filename}"):
                        os.remove(filepath)
                        if os.path.exists(txt_path): os.remove(txt_path)
                        st.rerun()
