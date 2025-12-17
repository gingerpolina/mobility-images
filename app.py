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

# Создаем папку для галереи, если её нет
GALLERY_DIR = "my_gallery"
if not os.path.exists(GALLERY_DIR):
    os.makedirs(GALLERY_DIR)

st.set_page_config(page_title="Urent Gen: Gold Edition", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen: Gold Edition")

# ==========================================
# 2. БРЕНДБУК (ПРОМПТЫ И СТИЛИ)
# ==========================================

# Стиль: Матовый "дорогой" пластик, минимализм, студийный свет
STYLE_PREFIX = (
    "((3D Product Render)), ((Claymorphism Style)), ((Matte Soft-Touch Plastic)). "
    "LOOK: Minimalist, Clean geometry, Toy-like but premium. "
    "LIGHTING: Studio softbox, global illumination, no harsh shadows."
)

STYLE_SUFFIX = "Made of matte plastic. Unreal Engine 5 render. Blender 3D."

# Анатомия Самоката (Kickboard - чтобы без сиденья)
SCOOTER_CORE = (
    "OBJECT: A modern Electric Kickboard (Stand-up vehicle). "
    "FORM: Thick vertical tube (Royal Blue), wide flat deck (Snow White). "
    "((NO SEAT)), ((NO SADDLE)). Standing only."
)

# Анатомия Машины
CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# Цвета и Фон
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Wires (#FF9601). NO PINK."
BACKGROUND = "BACKGROUND: ((Solid White Hex #FFFFFF)). No walls, no floor texture."
NEGATIVE_PROMPT = "photo, realistic, metal, chrome, seat, saddle, motorcycle, scooter, pink, purple, complex background, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    """
    Отправляет запрос к Pollinations.ai.
    Обрабатывает тайм-ауты и ошибки 429.
    """
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    
    try:
        # Для 4K (2048px) даем больше времени на ожидание (60 сек)
        timeout_val = 60 if width > 1024 else 30
        
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

tab1, tab2 = st.tabs(["🎨 Генератор", "📂 Галерея"])

# --- ВКЛАДКА 1: ГЕНЕРАТОР ---
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # ВАЖНО: Весь ввод внутри формы
        with st.form("generation_form"):
            st.header("Настройки")
            mode = st.radio("Тип объекта:", ["🛴 Самокат (Urent)", "🚗 Машина", "📦 Другое"])
            aspect = st.selectbox("Формат:", ["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Сториз)"])
            user_input = st.text_area("Окружение:", value="стоит рядом с уличным фонарем", height=100)
            
            # Кнопка отправки внутри формы
            submitted = st.form_submit_button("🚀 Сгенерировать", type="primary")

    with col2:
        if submitted and user_input:
            # 1. Перевод запроса на английский
            try:
                translator = GoogleTranslator(source='auto', target='en')
                scene_en = translator.translate(user_input)
            except:
                scene_en = user_input # Fallback, если переводчик недоступен
            
            # Чистим запрос от слов, вызывающих "мопеды"
            clean_scene = scene_en.replace("scooter", "").replace("bike", "")
            
            # 2. Сборка промпта (Конкатенация строк во избежание ошибок синтаксиса)
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
                
            # Кодируем для URL
            final_prompt = urllib.parse.quote(f"{raw_prompt} --no {NEGATIVE_PROMPT}")
            
            # 3. Выбор размеров
            base_s = 1024
            if "16:9" in aspect: 
                w, h = int(base_s * 1.2), int(base_s * 0.6)
            elif "9:16" in aspect: 
                w, h = int(base_s * 0.6), int(base_s * 1.2)
            else: 
                w, h = base_s, base_s
            
            seed = random.randint(1, 999999)

            # 4. Процесс генерации
            with st.spinner("Леплю из цифрового пластилина..."):
                img_bytes = generate_image(final_prompt, w, h, seed)

            if img_bytes == "BUSY":
                st.warning("Сервер перегружен (ошибка 429). Подождите 5-10 секунд и нажмите кнопку снова.")
            elif img_bytes:
                # Показываем результат
                image = Image.open(io.BytesIO(img_bytes))
                st.image(image, caption=f"Результат ({w}x{h})", use_container_width=True)
                
                # 5. Сохранение на диск
                # Формируем имя файла
                t_str = datetime.datetime.now().strftime("%H%M%S")
                final_filename = f"{t_str}_{seed}_{w}_{h}.png"
                filepath = os.path.join(GALLERY_DIR, final_filename)
                
                # Сохраняем картинку
                with open(filepath, "wb") as f:
                    f.write(img_bytes)
                
                # Сохраняем промпт в текстовый файл (нужен для апскейла)
                with open(filepath + ".txt", "w", encoding="utf-8") as f:
                    f.write(final_prompt)
                    
                st.toast("✅ Сохранено в галерею!")
                time.sleep(1) # Даем время записаться
                st.rerun()    # Обновляем страницу
            else:
                st.error("Ошибка соединения. Попробуйте еще раз.")

# --- ВКЛАДКА 2: ГАЛЕРЕЯ ---
with tab2:
    # Получаем список файлов (картинки)
    files = sorted([f for f in os.listdir(GALLERY_DIR) if f.endswith(".png")], reverse=True)
    
    if not files:
        st.info("В галерее пока пусто. Сгенерируйте первое изображение во вкладке 'Генератор'!")
    else:
        st.write(f"Сохранено работ: {len(files)}")
        
        # Сетка в 2 колонки
        cols = st.columns(2)
        
        for i, filename in enumerate(files):
            filepath = os.path.join(GALLERY_DIR, filename)
            txt_path = filepath + ".txt"
            
            # Парсим имя файла: время_сид_ширина_высота.png
            try:
                parts = filename.replace(".png", "").split("_")
                seed = int(parts[1])
                width = int(parts[2])
                height = int(parts[3])
                # Если ширина > 1500, значит это уже 4K
                is_4k = width > 1500
            except:
                seed = 0; width = 1024; height = 1024; is_4k = False

            # Вывод карточки
            with cols[i % 2]:
                with st.container(border=True):
                    try:
                        img = Image.open(filepath)
                        st.image(img, use_container_width=True)
                    except:
                        st.error("Ошибка чтения файла")
                        continue

                    # Метки качества
                    if is_4k:
                        st.caption(f"💎 **Ultra HD (4K)** | {width}x{height}")
                    else:
                        st.caption(f"🔹 Standard | {width}x{height}")
                    
                    # Кнопки (в ряд)
                    c1, c2, c3 = st.columns([1, 1.5, 0.5])
                    
                    # 1. СКАЧАТЬ
                    with open(filepath, "rb") as f:
                        c1.download_button("⬇️", f, filename, "image/png", key=f"dl_{filename}")

                    # 2. УЛУЧШИТЬ (Только для обычных картинок)
                    if not is_4k:
                        if c2.button("✨ В 4K", key=f"up_{filename}", help="Перерисовать в высоком качестве (занимает ~40 сек)"):
                            # Проверяем, есть ли сохраненный промпт
                            if os.path.exists(txt_path):
                                with open(txt_path, "r", encoding="utf-8") as f:
                                    saved_prompt = f.read()
                                
                                with st.spinner("Генерация 4K версии..."):
                                    # Удваиваем разрешение
                                    new_w, new_h = width * 2, height * 2
                                    hq_bytes = generate_image(saved_prompt, new_w, new_h, seed)
                                    
                                    if hq_bytes and hq_bytes != "BUSY":
                                        # Создаем новый файл
                                        new_name = filename.replace(f"_{width}_{height}", f"_{new_w}_{new_h}")
                                        new_path = os.path.join(GALLERY_DIR, new_name)
                                        
                                        # Записываем новую картинку
                                        with open(new_path, "wb") as f: 
                                            f.write(hq_bytes)
                                        # Копируем файл промпта к новому имени
                                        shutil.copy(txt_path, new_path + ".txt")
                                        
                                        # Удаляем старую (маленькую) версию
                                        os.remove(filepath)
                                        os.remove(txt_path)
                                        
                                        st.rerun() # Обновляем интерфейс
                                    else:
                                        st.error("Сервер занят, попробуйте позже.")
                            else:
                                st.error("Ошибка: исходный промпт не найден.")

                    # 3. УДАЛИТЬ
                    if c3.button("🗑️", key=f"del_{filename}"):
                        os.remove(filepath)
                        if os.path.exists(txt_path): 
                            os.remove(txt_path)
                        st.rerun()
