# prompts.py

# --- 1. СТИЛЬ ---
STYLE_PREFIX = """((NO REALISM)). 3D minimalist product render. Style: Matte plastic textures, smooth rounded shapes, soft studio lighting, ambient occlusion. Aesthetic: Playful, modern, high fidelity, C4D style, Octane render."""
STYLE_SUFFIX = """High quality 3D render. 4k resolution."""

# --- 2. КОМПОЗИЦИЯ (Усиленная группировка) ---
# Добавлено: "All elements are visually connected" и "Camera Zoom Out"
COMPOSITION_RULES = """VIEW: Wide Long Shot. COMPOSITION: The Main Object + The Rider + The Environment Props form a SINGLE VISUAL GROUP in the center. MARGINS: Add 20% empty background padding around this ENTIRE GROUP. The scooter wheels and the rider's head must be far from the image edges. Zoom out to fit the whole scene."""

# --- 3. АНАТОМИЯ ТРАНСПОРТА ---
SCOOTER_CORE = """MAIN OBJECT: Modern Electric Kick Scooter. DESIGN: 1. Tall vertical Blue tube (Steering stem) with T-handlebars. 2. Wide, seamless, low-profile unibody standing deck (Snow White). 3. Small minimalist wheels partially enclosed. SHAPE: Sleek, integrated, geometric L-shape. ((NO SEAT))."""
CAR_CORE = """MAIN OBJECT: Cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."""

# --- 4. ЦВЕТА ---
COLOR_RULES = """COLORS: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."""

# --- 5. НЕГАТИВНЫЙ ПРОМПТ ---
# Добавлено: "floating, flying"
NEGATIVE_PROMPT = """realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, bench, sitting, kneeling, four legs, crawling, moped, motorcycle, cut off, cropped, text, watermark, levitation, hovering feet, jumping, flying, floating, white body, fat, obese, round tummy, short legs"""

# --- 6. ПАССАЖИР (v43.0: ГРАВИТАЦИЯ) ---
PASSENGER_START = "RIDER: A cute 3D plastic toy character of "

# Тело: Натуральные цвета, без живота, длинные ноги
PASSENGER_BODY = ". BODY SHAPE: Universal simplified vinyl toy shape. Anthropomorphic, athletic build. COLOR: Natural characteristic colors of the animal. NOT all white. PROPORTIONS: Balanced. Legs are LONG ENOUGH to reach the deck while holding handles. Normal torso (no round tummy). "

# Физика: Гравитация + Контакт
PASSENGER_PHYSICS = "PHYSICS: HEAVY WEIGHT. The character is pressed down onto the scooter by gravity. POSE: Standing firmly. FEET: SOLES ARE GLUED TO THE DECK. Zero gap between feet and deck. Cast shadows directly under the feet. ARMS: Arms extended forward to grip the handlebars. STANCE: One leg slightly ahead of the other for balance."

PASSENGER_EMPTY = "No rider. Empty flat deck. ((NO SEAT))."
