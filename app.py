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
# 1. НАСТРОЙКИ
# ==========================================

GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen v20 (Studio)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v20: Студийный Свет")

if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. БРЕНДБУК
# ==========================================

# СТИЛЬ: Матовый пластик, Идеальная форма
STYLE_PREFIX = (
    "((NO REALISM)). ((Matte Plastic Toy World)). ((3D Claymorphism)). "
    "LOOK: Minimalist, Smooth rounded edges, Clean geometry. "
    "MATERIAL: Soft-touch matte plastic everywhere. "
    "LIGHTING: Flat studio lighting, evenly lit. "
)

STYLE_SUFFIX = "Everything is made of matte plastic. Unreal Engine 5. Blender 3D."

# АНАТОМИЯ: L-SHAPE (Чтобы не было кресла)
SCOOTER_CORE = (
    "OBJECT: A modern Electric Kick Scooter. "
    "SILHOUETTE: ((Strict L-Shaped profile)). "
    "ANATOMY: 1. Tall vertical steering stem (Royal Blue). 2. Flat low deck for standing (Snow White). 3. Two small wheels. "
    "((NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). "
    "The deck is completely flat and empty. Standing mode only. "
)

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# ЦВЕТА
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Details (#FF9601). NO PINK."

# НЕГАТИВ (Против теней и градиентов)
NEGATIVE_PROMPT = "(shadow:2.0), (cast shadow:2.0), (gradient:2.0), (vignette:2.0), (shading:1.5), (seat:3.0), (saddle:3.0), moped, realistic, photo, metal, chrome, reflection, dirt, pink, purple, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    # Запрашиваем генерацию
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        timeout_val = 80 if width > 1200 else 30
        response = requests.get(url, timeout=timeout_val)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
            return None
    except:
        return None

def smart_resize(image_bytes, target_w, target_h):
    """
    Если сервер вернул картинку меньше, чем мы хотели,
    мы растягиваем её сами методом LANCZOS (лучшее качество).
    """
    img = Image.open(io.BytesIO(image_bytes))
    current_w, current_h = img.size
    
    # Если картинка меньше цели, делаем ресайз
    if current_w < target_w or current_h < target_h:
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
    # Возвращаем байты
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==========================================
# 4. ИНТЕРФЕЙС
# ==========================================

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# --- ВКЛАДКА 1: ГЕНЕРАТОР ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.form("gen_form"):
            st.subheader("Настройки")
            mode = st.radio("Объект:", ["🛴 Самокат", "🚗 Машина", "📦 Другое"])
            
            # НОВЫЕ ФОНЫ (Только плоские цвета)
            bg_select = st.selectbox("Студийный Фон (Без теней):", [
                "⬜ Белый (Flat White)", 
                "🟦 Синий Бренд (#0668D7)",
                "🟧 Оранжевый Бренд (#FF9601)",
                "⬛ Черный Матовый (Black)"
            ])
            
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Детали (необязательно):", height=80)
            
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted:
            # 1. Перевод
            try:
                translator = GoogleTranslator(source='auto', target='en')
                if user_input:
                    scene_en = translator.translate(user_input)
                else:
                    scene_en = "minimalist studio shot"
            except:
                scene_en = user_input if user_input else "minimalist studio shot"
            
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            # 2. ПЛОСКИЙ ФОН (Строгие правила)
            if "Белый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat White Color Hex #FFFFFF)). ((2D Background)). ((NO SHADOWS)). ((NO GRADIENT)). Isolated."
            elif "Синий" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Royal Blue Color Hex #0668D7)). ((2D Background)). ((NO SHADOWS)). ((NO GRADIENT))."
            elif "Оранжевый" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Neon Orange Color Hex #FF9601)). ((2D Background)). ((NO SHADOWS)). ((NO GRADIENT))."
            elif "Черный" in bg_select:
                bg_prompt = "BACKGROUND: ((Solid Flat Matte Black Color Hex #000000)). ((2D Background)). ((NO SHADOWS)). ((NO GRADIENT))."

            # 3. Сборка промпта
            if "Самокат" in mode:
                scene_context = f"SCENE: {clean_scene}. The object has a strict L-shaped silhouette."
                raw_prompt = f"{STYLE_PREFIX} {SCOOTER_CORE} {scene_context} {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            elif "Машина" in mode:
                raw_prompt = f"{STYLE_PREFIX} {CAR_CORE} SCENE: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            else:
                raw_prompt = f"{STYLE_PREFIX} OBJECT: {clean_scene}. {COLOR_RULES} {bg_prompt} {STYLE_SUFFIX}"
            
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 4. Размеры
            base_s = 1024
            if "16:9" in aspect: w, h = int(base_s*1.2), int(base_s*0.6)
            elif "9:16" in aspect: w, h = int(base_s*0.6), int(base_s*1.2)
            else: w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 5. Запрос
            with st.spinner("Рендер без теней..."):
                img_bytes = generate_image(final_prompt, w, h, seed)
            
            if img_bytes == "BUSY":
                st.warning("Сервер занят. Подождите пару секунд.")
            elif img_bytes:
                st.session_state.last_image_bytes = img_bytes
                st.session_state.last_image_size = (w, h)
                
                # Сохраняем
                t_str = datetime.datetime.now().strftime("%H%M%S")
                fn = f"{t_str}_{seed}_{w}_{h}.png"
                fp = os.path.join(GALLERY_DIR, fn)
                
                with open(fp, "wb") as f: f.write(img_bytes)
                with open(fp + ".txt", "w", encoding="utf-8") as f: f.write(final_prompt)
                
                st.rerun()
            else:
                st.error("Ошибка сети.")

        # ОТОБРАЖЕНИЕ
        if st.session_state.last_image_bytes:
            st.success("Готово!")
            img = Image.open(io.BytesIO(st.session_state.last_image_bytes))
            st.image(img, caption=f"Результат ({st.session_state.last_image_size[0]}x{st.session_state.last_image_size[1]})", use_container_width=True)

# --- ВКЛАДКА 2: ГАЛЕРЕЯ ---
with tab2:
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    if not files:
        st.info("Галерея пуста.")
    else:
        st.write(f"Работ в галерее: {len(files)}")
        cols = st.columns(2)
        for i, filename in enumerate(files):
            fp = os.path.join(GALLERY_DIR, filename)
            tp = fp + ".txt"
            
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
            except: seed = 0

            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        img = Image.open(fp)
                        rw, rh = img.size
                        st.image(img, use_container_width=True)
                    except: continue

                    # Статус качества
                    if rw >= 2000:
                        st.caption(f"💎 **4K (Upscaled)** | {rw}x{rh}")
                        can_up = False
                    else:
                        st.caption(f"🔹 Base | {rw}x{rh}")
                        can_up = True
                    
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    with open(fp, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"d{i}")
                    
                    if can_up:
                        # КНОПКА ГИБРИДНОГО АПСКЕЙЛА
                        if c2.button("✨ Сделать 2048px", key=f"u{i}"):
                            if os.path.exists(tp):
                                with open(tp, "r", encoding="utf-8") as f: p = f.read()
                                
                                with st.spinner("Запрос 4K + Smart Resize..."):
                                    # 1. Просим у сервера честные 2048
                                    target_w, target_h = 2048, 2048
                                    hq_bytes = generate_image(p, target_w, target_h, seed)
                                    
                                    if hq_bytes and hq_bytes != "BUSY":
                                        # 2. ПРИНУДИТЕЛЬНЫЙ РЕСАЙЗ ДО 2048
                                        # (Если сервер вернул 1024, мы сами растянем до 2048)
                                        final_bytes = smart_resize(hq_bytes, target_w, target_h)
                                        
                                        # 3. Сохраняем результат который ТОЧНО 2048
                                        n_name = filename.replace(f"_{rw}_{rh}", f"_{target_w}_{target_h}")
                                        n_path = os.path.join(GALLERY_DIR, n_name)
                                        
                                        with open(n_path, "wb") as f: f.write(final_bytes)
                                        shutil.copy(tp, n_path + ".txt")
                                        
                                        os.remove(fp); os.remove(tp)
                                        st.rerun()
                                    else:
                                        st.error("Сервер занят.")
                            else: st.error("Нет данных.")
                    
                    if c3.button("🗑️", key=f"x{i}"):
                        os.remove(fp)
                        if os.path.exists(tp): os.remove(tp)
                        st.rerun()
