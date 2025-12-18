# prompts.py

# --- 1. СТИЛЬ ---
STYLE_PREFIX = """((NO REALISM)). 3D minimalist product render. Style: Matte plastic textures, smooth rounded shapes, soft studio lighting, ambient occlusion. Aesthetic: Playful, modern, high fidelity, C4D style, Octane render."""
STYLE_SUFFIX = """High quality 3D render. 4k resolution."""

# --- 2. КОМПОЗИЦИЯ ---
COMPOSITION_RULES = """VIEW: Long shot (Full Body). COMPOSITION: The Main Object, the Rider, and the Environmental Props are GROUPED together in the center. MARGINS: Leave 20% empty background padding around this ENTIRE GROUP. Ensure trees and props are NOT cut off. Zoom out."""

# --- 3. АНАТОМИЯ ТРАНСПОРТА ---
SCOOTER_CORE = """MAIN OBJECT: Modern Electric Kick Scooter. DESIGN: 1. Tall vertical Blue tube (Steering stem) with T-handlebars. 2. Wide, seamless, low-profile unibody standing deck (Snow White). 3. Small minimalist wheels partially enclosed. SHAPE: Sleek, integrated, geometric L-shape. ((NO SEAT))."""
CAR_CORE = """MAIN OBJECT: Cute chunky autonomous white sedan car, blue branding stripe, smooth plastic body."""

# --- 4. ЦВЕТА ---
COLOR_RULES = """COLORS: Matte Snow White Body, Royal Blue Stem (#0668D7), Neon Orange Accents (#FF9601). NO PINK."""

# --- 5. НЕГАТИВНЫЙ ПРОМПТ ---
NEGATIVE_PROMPT = """realistic, photo, grain, noise, dirt, grunge, metal reflection, seat, saddle, chair, bench, sitting, kneeling, four legs, crawling, moped, motorcycle, cut off, cropped, text, watermark, levitation, hovering feet, jumping, white body"""

# --- 6. ПАССАЖИР (v42.0: Натуральные цвета + СТОЯТЬ!) ---
# Часть 1: Вступление
PASSENGER_START = "RIDER: A cute 3D plastic toy character of "

# Часть 2: Описание тела (Натуральные цвета)
PASSENGER_BODY = ". BODY SHAPE: Universal simplified round vinyl toy shape. Chubby, anthropomorphic, minimalistic. COLOR: Natural characteristic colors of the animal/character (e.g. Brown for Bear, Orange for Fox, Grey for Mouse). NOT all white. PROPORTIONS: Short legs, round tummy, large simplified head. FACE: Minimalist. Eyes are simple small BLACK DOTS (pimpules). "

# Часть 3: Поза и Масштаб (СТОЯТЬ!)
PASSENGER_PHYSICS = "POSE: STANDING UPRIGHT on the deck. RIDING STANDING UP. NOT SITTING. SCALE: The character is large. SHOULDERS MUST BE HIGHER than the scooter handlebars. ARMS: Arms extended, HANDS FIRMLY GRIPPING THE T-HANDLEBARS. LEGS: ONE LEG PLACED SLIGHTLY AHEAD OF THE OTHER. FEET: SOLES OF FEET FLAT ON THE DECK SURFACE. ZERO GAP."

# Если пассажира нет
PASSENGER_EMPTY = "No rider. Empty flat deck. ((NO SEAT))."
