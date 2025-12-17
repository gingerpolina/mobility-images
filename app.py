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

st.set_page_config(page_title="Urent Gen v17.1 (Blue BG)", layout="wide", page_icon="🛴")
st.title("🛴 Urent Gen v17.1: Фирменный Фон")

# Инициализация состояния (чтобы картинка не исчезала)
if 'last_image_bytes' not in st.session_state:
    st.session_state.last_image_bytes = None
if 'last_image_size' not in st.session_state:
    st.session_state.last_image_size = (0, 0)

# ==========================================
# 2. ПАРАМЕТРЫ СТИЛЯ (БРЕНДБУК)
# ==========================================

# СТИЛЬ: Игрушечный мир
STYLE_PREFIX = (
    "((NO REALISM)). ((3D Claymorphism Render)), ((Matte Soft Plastic Material)). "
    "LOOK: Cute, Minimalist, Smooth rounded edges, Toy-like proportions. "
    "LIGHTING: Bright Softbox lighting, clean shadows. "
)

STYLE_SUFFIX = "Everything is made of matte plastic. Unreal Engine 5. Blender 3D."

# АНАТОМИЯ: СКЕЙТ С РУЧКОЙ (Убиваем сиденье)
SCOOTER_CORE = (
    "OBJECT: A modern Stand-up Electric Kickboard. "
    "ANATOMY: A flat skateboard-like deck (Snow White) + A vertical T-bar handle (Royal Blue). "
    "((STRICTLY NO SEAT)), ((NO SADDLE)), ((NO CHAIR)). "
    "The object is designed for STANDING only. "
)

CAR_CORE = "OBJECT: Minimalist autonomous white sedan, blue stripe, matte plastic body."

# ЦВЕТА
COLOR_RULES = "PALETTE: Matte Snow White Body, Royal Blue Accents (#0668D7), Neon Orange Details (#FF9601). NO PINK."

# НЕГАТИВ (Вес 3.0 на сиденья)
NEGATIVE_PROMPT = "(seat:3.0), (saddle:3.0), (chair:3.0), moped, vespa, motorcycle, realistic, photo, metal, chrome, reflection, dirt, grunge, pink, purple, text, watermark"

# ==========================================
# 3. ФУНКЦИИ
# ==========================================

def generate_image(prompt, width, height, seed, model='flux'):
    url = f"https://pollinations.ai/p/{prompt}?width={width}&height={height}&model={model}&nologo=true&enhance=false&seed={seed}"
    try:
        # Для HD даем больше времени
        timeout_val = 80 if width > 1200 else 30
        response = requests.get(url, timeout=timeout_val)
        
        if response.status_code == 200:
            return response.content
        elif response.status_code == 429:
            return "BUSY"
        else:
