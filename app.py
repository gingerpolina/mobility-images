import streamlit as st
import requests
from PIL import Image
import io
import urllib.parse
import random
import time
import os
import datetime

# !!! ВАЖНО: Импортируем файл с промптами !!!
import prompts

# --- НАСТРОЙКИ ---
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

# Исправленная строка конфигурации (layout="wide")
st.set_page_config(page_title="Scooter Gen v39.2", layout="wide", page_icon="🛴")
st.title("🛴 Scooter Gen v39.2: Modular Architecture")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# Безопасный импорт переводчика
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# --- ФУНКЦИИ ---
def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=45)
            if response.status_code == 200:
                return response.content
            elif response.status_code == 429:
                time.sleep(2 + attempt * 2)
                continue
        except:
            time.sleep(2 + attempt * 2)
            continue
    return None

def generate_image(prompt, width, height, seed, model='flux'):
    encoded_prompt = urllib.parse.quote(prompt)
    url = "https://pollinations.ai/p/" + encoded_prompt + "?width=" + str(width) + "&height=" + str(height) + "&model=" + model + "&nologo=true&enhance=true&seed=" + str(seed)
    return make_request_with_retry(url)

def smart_resize(image_bytes, target_w, target_h):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.size[0] < target_w or img.size[1] < target_h:
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except:
        return image_bytes

def translate_text(text):
    if not text or not HAS_TRANSLATOR:
        return text
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except:
        return text

# --- ИНТЕРФЕЙС ---
tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            passenger_input = st.text_input("👤 Пассажир:", placeholder="Например: Кот...")
            st.divider()
            
            color_theme = st.selectbox("🎨 Окружение:", [
                "🟦 Royal Blue", 
                "⬜ Flat White", 
                "🟧 Neon Orange", 
                "🎨 Natural", 
                "⬛ Matte Black"
            ])
            
            env_input = st.text_area("🌳 Детали окружения:", height=80)
            aspect = st.selectbox("Формат:", ["1:1", "16:9", "9:16"])
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            env_en = translate_text(env_input) if env_input else ""
            pass_en = translate_text(passenger_input) if passenger_input else ""

            # --- СБОРКА ПРОМПТА (ИЗ МОДУЛЯ) ---
            
            # 1. ПАССАЖИР
            if pass_en:
                if "Самокат" in mode:
                    # Собираем через плюс (безопасно)
                    passenger_prompt = prompts.PASSENGER_START + pass_en + prompts.PASSENGER_BODY + prompts.PASSENGER_PHYSICS
                else:
                    passenger_prompt = "CHARACTER: A cute 3D plastic toy character of " + pass_en + "."
            else:
                passenger_prompt = prompts.PASSENGER_EMPTY

            # 2. ФОН
            if "Blue" in color_theme:
                bg_data = "BACKGROUND: Seamless Royal Blue Studio Cyclorama #0668D7. Uniform background. ENV MATERIAL: Matte Blue Plastic."
            elif "Orange" in color_theme:
                bg_data = "BACKGROUND: Seamless Neon Orange Studio Cyclorama #FF9601. Uniform background. ENV MATERIAL: Matte Orange Plastic."
            elif "White" in color_theme:
                bg_data = "BACKGROUND: Seamless Flat White Studio Cyclorama. Uniform background. ENV MATERIAL: Matte White Plastic."
            elif "Black" in color_theme:
                bg_data = "BACKGROUND: Seamless Matte Black Studio Cyclorama. Uniform background. ENV MATERIAL: Dark Grey Plastic."
            else:
                bg_data = "BACKGROUND: Soft Studio Lighting. ENV MATERIAL: Colorful matte plastic."

            if env_en:
                full_env = "SCENE: " + env_en + ". " + bg_data
            else:
                full_env = "SCENE: Isolated studio shot. " + bg_data
            
            # 3. ОБЪЕКТ
            if "Самокат" in mode:
                core = prompts.SCOOTER_CORE
            elif "Машина" in mode:
                core = prompts.CAR_CORE
            else:
                core = "MAIN OBJECT: " + env_en

            # 4. ФИНАЛ
            # Простое сложение строк
            raw_prompt = prompts.STYLE_PREFIX + " " + prompts.COMPOSITION_RULES + " " + core + " " + passenger_prompt + " " + full_env + " " + prompts.COLOR_RULES + " " + prompts.STYLE_SUFFIX
            final_prompt = raw_prompt + " --no " + prompts.NEGATIVE_PROMPT
            
            # Размеры
            base_s = 1024
            if "16:9" in aspect:
                w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect:
                w, h = int(base_s*0.6), int(base_s*1.2)
            else:
                w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            status = st.empty()
            status.info("🔄 Стучимся к серверу...")
            
            img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes:
                status.success("✅ Готово!")
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = t_str + "_" + str(seed) + "_" + str(w) + "_" + str(h) + ".png"
                fp = os.path.join(GALLERY_DIR, fn)
                
                with open(fp, "wb") as f:
                    f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                
                time.sleep(0.5)
                st.rerun()
            else:
                status.error("❌ Сервер перегружен.")

        if st.session_state.last_image_bytes:
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption="Результат", use_container_width=True)

# --- ГАЛЕРЕЯ ---
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    if not files:
        st.info("Пусто.")
    else:
        st.write("Всего: " + str(len(files)))
        cols = st.columns(2)
        for i, filename in enumerate(files):
            fp = os.path.join(GALLERY_DIR, filename)
            tp = fp + ".txt"
            
            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        img = Image.open(fp)
                        st.image(img, use_container_width=True)
                    except:
                        continue
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    with open(fp, "rb") as f:
                        c1.download_button("⬇️", f, filename)
                    
                    rw, rh = img.size
                    if rw < 2000:
                        if c2.button("✨ 2048px", key="u"+str(i)):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f:
                                    p = f.read()
                                st.toast("⏳ Улучшаем...")
                                try:
                                    old_seed = int(filename.split("_")[1])
                                except:
                                    old_seed = random.randint(1, 99999)
                                
                                hq_bytes = generate_image(p, 2048, 2048, old_seed)
                                if hq_bytes:
                                    final_bytes = smart_resize(hq_bytes, 2048, 2048)
                                    n_path = os.path.join(GALLERY_DIR, filename.replace(str(rw)+"_"+str(rh), "2048_2048"))
                                    with open(n_path, "wb") as f:
                                        f.write(final_bytes)
                                    with open(n_path + ".txt", "w", encoding="utf-8") as f:
                                        f.write(p)
                                    
                                    os.remove(fp)
                                    os.remove(tp)
                                    st.rerun()
                                else:
                                    st.error("Сервер занят")
                            else:
                                st.error("Нет промпта")
                    
                    if c3.button("🗑️", key="x"+str(i)):
                        os.remove(fp)
                        if os.path.exists(tp):
                            os.remove(tp)
                        st.rerun()
