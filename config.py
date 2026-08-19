# =============================================================================
# config.py — All configurable parameters for the Matrix Camera App
# =============================================================================

# --- Camera ---
CAMERA_INDEX = 0          # Webcam device index (0 = default)
MIRROR_CAMERA = True      # Flip horizontally for selfie-style view

# --- Window ---
WINDOW_WIDTH    = 1280
WINDOW_HEIGHT   = 720
FULLSCREEN      = False

# --- Performance & FPS Settings ---
# FPS_TARGET: Set to 0 for UNCAPPED / MAXIMUM FPS (runs as fast as your GPU/CPU allows!)
# Set to 30, 60, 120, 144, 240, or 0 for MAX FPS.
FPS_TARGET      = 30       # 0 = UNCAPPED MAX FPS (No frame rate limit)
MAX_FPS_MODE    = True    # Enable C-level batch surface blitting and SIMD fast resize
USE_FAST_BLIT   = True    # Batch Pygame SDL blitting (up to 5x higher FPS at high column counts)

# --- ASCII Rendering ---
ASCII_COLS      = 500     # Number of character columns (horizontal resolution)
FONT_SIZE       = 6       # Pixel size of the monospaced font
FONT_NAME       = None    # None = use bundled fallback; set to a file path or system name

# Standard brightness ramp — darker pixels → sparser chars, brighter → denser
ASCII_RAMP = " .:-=+*#%@"

# Matrix-flavored character set used when Matrix mode randomizes characters
MATRIX_CHARSET = "01ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%&*@!?><|"

# --- Image Processing ---
CONTRAST          = 1.25   # Multiplier applied to pixel values (>1 increases contrast)
BRIGHTNESS        = 10    # Additive offset applied after contrast scaling
USE_CLAHE         = True  # Adaptive contrast equalization — brings out crisp facial features
CLAHE_CLIP_LIMIT  = 3.0   # Higher value = more localized facial detail contrast
INVERT_GAMMA      = 0.75  # Gamma multiplier for Invert mode — prevents blown-out facial highlights

# --- Matrix Rain ---
RAIN_ENABLED      = True
RAIN_DENSITY      = 0.04   # Fraction of columns that spawn a new stream per frame
RAIN_SPEED_MIN    = 1      # Minimum cells per frame a stream advances
RAIN_SPEED_MAX    = 3      # Maximum cells per frame a stream advances
RAIN_LENGTH_MIN   = 6      # Minimum stream length in characters
RAIN_LENGTH_MAX   = 28     # Maximum stream length in characters
RAIN_ALPHA        = 180    # Opacity of the rain overlay surface (0–255)

# --- Colours (R, G, B) ---
COLOR_BG          = (0,   0,   0)     # Background
COLOR_ASCII_DARK  = (0,   80,  0)     # Darkest ASCII characters
COLOR_ASCII_MID   = (0,   180, 40)    # Mid-brightness characters
COLOR_ASCII_BRIGHT= (140, 255, 100)   # Brightest characters
COLOR_RAIN_HEAD   = (220, 255, 220)   # Leading character of a rain stream
COLOR_RAIN_BODY   = (0,   200, 50)    # Main stream body
COLOR_RAIN_FADE   = (0,   60,  15)    # Tail / fading part
COLOR_HUD         = (0,   210, 60)    # HUD text colour
COLOR_HUD_DIM     = (0,   110, 30)    # Dimmer HUD elements

# --- Silhouette & Light Background / Invert Mode ---
# INVERT_MODE: Smart Light-BG Mode (toggled at runtime with the I key)
# Suppresses bright background walls/windows into black space while rendering
# the human subject with natural green shading (skin = bright, eyes/hair = dark contours).
INVERT_MODE          = False   # toggled at runtime with the I key
LIGHT_BG_CUTOFF_PCT  = 78      # Percentile threshold to isolate light background wall (70-85%)
SILHOUETTE_MODE      = False   # toggled at runtime with the V key
SILHOUETTE_BOOST     = 2.0     # brightness multiplier applied to foreground chars
SILHOUETTE_THRESHOLD = 0.30    # Otsu fallback threshold (used only during BG warmup)
BG_WARMUP_FRAMES     = 120     # frames MOG2 needs to learn the background (~4 s at 30 fps)

# --- HUD ---
HUD_FONT_SIZE = 14
SHOW_HUD      = True
