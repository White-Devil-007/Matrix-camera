# Matrix Camera — Digital Rain Webcam ASCII Art

A real-time Python desktop application that converts your live webcam feed into a **Matrix-style ASCII art** display with a **digital rain overlay**.

---

## Screenshot / Preview

```
@@@@@#*+:.       .:+*#@@@@@    ░ 0 1 A B      1 A   ░
@@@#*+:.   (you)   .:+*#@@@    B   ░ 0       ░ Z 1   
@@#*:.   .-====-.    .:*#@@    ░     ░   0 A       ░ 
```

> Every character is generated live from your webcam — nothing is faked.

---

## Requirements

| Package           | Minimum version |
|-------------------|-----------------|
| Python            | 3.10+           |
| opencv-python     | 4.8.0           |
| pygame            | 2.5.0           |
| numpy             | 1.24.0          |

---

## Installation

```bash
# 1. Clone / download the project
cd matrix_camera

# 2. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

## Running Locally (Desktop)

```bash
python main.py
```

---

## Deployment (Windows & Mobile / iOS / Android)

### Option 1: Mobile & Web Deployment (Cross-Device PWA)

To run live on your **iPhone, Android, Tablet, or Web Browser**:

1. **Host on local Wi-Fi network**:
   ```bash
   python server.py
   ```
   Open the displayed Mobile URL (e.g., `http://192.168.1.X:8000`) on your smartphone connected to the same Wi-Fi!

2. **One-Click Cloud Deployment (Vercel / Netlify / GitHub Pages)**:
   Deploy the `web/` folder directly to Vercel, Netlify, or GitHub Pages.
   - PWA Enabled: Mobile users can tap **"Add to Home Screen"** to install it as a fullscreen native smartphone app!
   - Includes Front/Rear camera flip button, touch controls, Smart Light-BG Invert, and Silhouette mode.

### Option 2: Windows Standalone Executable (.exe)

Package into a standalone Windows `.exe` file (no Python required on target machines):

```bash
python build_desktop.py
```
The compiled executable will be located in `dist/MatrixCamera/MatrixCamera.exe`.

The window opens immediately. If no webcam is found, an error message is shown for 5 seconds then the app exits.

---

## Controls

| Key          | Action                              |
|--------------|-------------------------------------|
| `ESC` / `Q`  | Quit                                |
| `SPACE`      | Pause / Resume camera               |
| `C`          | Toggle camera ASCII rendering       |
| `M`          | Toggle Matrix rain overlay          |
| `V`          | **Toggle Silhouette Mode**          |
| `I`          | **Toggle Invert / Light BG Mode**   |
| `R`          | Reset / randomise rain streams      |
| `F`          | Toggle fullscreen                   |
| `S`          | Save screenshot (PNG in CWD)        |
| `+` / `-`    | Increase / decrease ASCII columns   |
| `H`          | Show / hide help overlay            |

---

## Configuration

All tunable parameters live in **`config.py`**.  
The most useful ones:

| Variable         | Default | Description                                             |
|------------------|---------|---------------------------------------------------------|
| `FPS_TARGET`     | `0`     | **Target FPS (`0` = UNCAPPED MAX FPS, `30`, `60`, `120`, `240`)** |
| `MAX_FPS_MODE`   | `True`  | **Enables C-level batch surface blitting and OpenCV SIMD resize** |
| `USE_FAST_BLIT`  | `True`  | **Uses Pygame SDL C-level batch `blits()` for 5x frame rate boost** |
| `ASCII_COLS`     | `500`   | Horizontal character resolution (more = finer detail)   |
| `FONT_SIZE`      | `4`     | Pixel size of each character                            |
| `USE_CLAHE`      | `True`  | Local adaptive contrast enhancement for facial detail   |
| `INVERT_MODE`    | `False` | Inverts brightness for light backgrounds (`I` key)      |
| `SILHOUETTE_MODE`| `False` | Cuts out static background via MOG2 (`V` key)           |
| `CONTRAST`       | `1.3`   | Frame contrast multiplier                               |
| `BRIGHTNESS`     | `5`     | Pixel value offset after contrast                       |
| `RAIN_DENSITY`   | `0.04`  | Probability of a new stream starting each frame         |
| `RAIN_ALPHA`     | `180`   | Rain overlay opacity (0 = invisible, 255 = opaque)      |

---

## Silhouette Mode

Press **`V`** at any time to toggle Silhouette Mode.
Background pixels below threshold become pure black space; you glow as vivid green characters.

Three toggle switches are always visible in the top-left HUD:
```
FPS   28
COLS 160
CAMERA  [●━━]   ← pill switch, green = ON
MATRIX  [●━━]
SILHOU  [━━●]   ← dark = OFF
```

### Tuning silhouette quality

- **Too much background showing?** Lower `SILHOUETTE_THRESHOLD` (e.g. `0.20`) — cuts off dimmer background pixels.
- **Your face disappearing?** Raise `SILHOUETTE_THRESHOLD` (e.g. `0.40`) — keeps more bright pixels.
- **Foreground looks dim?** Raise `SILHOUETTE_BOOST` (e.g. `2.2`) — stretches foreground contrast more aggressively.
- **Lighting tip:** Sit facing a light source. A dark background behind you gives the cleanest silhouette separation.

---

## How the Pipeline Works

```
Webcam
  │
  ▼  cv2.VideoCapture.read()
BGR frame (e.g. 720×1280×3 uint8)
  │
  ▼  Grayscale via luminance weighting (NumPy)
Grayscale float32 (720×1280)
  │
  ▼  Contrast + Brightness (NumPy)
Enhanced grayscale
  │
  ▼  Nearest-neighbour downsample (NumPy index tricks)
Small grid  (rows × ascii_cols)   e.g. 45×160
  │
  ┌──────────────────────────────────────────┐
  │  SILHOUETTE_MODE off (Normal)             │
  │  Index into MATRIX_CHARSET full ramp      │
  │  Colour: 3-stop green gradient            │
  └──────────────────────────────────────────┘
  │       OR
  ┌──────────────────────────────────────────┐
  │  SILHOUETTE_MODE on                       │
  │  Pixels < THRESHOLD → space (invisible)   │
  │  Pixels ≥ THRESHOLD → boosted, dense char │
  │  Colour: all chars use COLOR_ASCII_BRIGHT │
  └──────────────────────────────────────────┘
  │
  ▼  ASCIIRenderer.render() — pre-cached Pygame glyphs
ASCII image on Pygame surface
  │
  ▼  MatrixRain.update() + MatrixRain.render()
Rain overlay (RGBA, alpha-blended)
  │
  ▼  HUD blit (FPS + pill toggle switches)
  │
  ▼  pygame.display.flip()
Final window frame
```

### Key design decisions

- **Glyph cache (`GlyphCache`)** — every `(char, colour)` pair is pre-rendered once at startup. The hot loop only calls `surface.blit()`, never `font.render()`.
- **NumPy-only preprocessing** — the entire grayscale conversion, contrast/brightness adjustment, and nearest-neighbour downsample use vectorised NumPy operations; no Python-level pixel loops.
- **RGBA rain surface** — the rain is drawn on a separate `SRCALPHA` surface and alpha-blended each frame, so the camera image remains visible underneath.
- **Stochastic stream spawning** — new streams are created probabilistically (`RAIN_DENSITY` × cols) each frame, giving the screen a natural, organic feel.

---

## Troubleshooting

### "Cannot open webcam"

1. Check that your webcam is physically connected and not used by another app (Teams, Zoom, etc.).
2. On Windows, open **Settings → Privacy → Camera** and ensure Python / the terminal has permission.
3. Try changing `CAMERA_INDEX` in `config.py` to `1`, `2`, etc. if you have multiple cameras.
4. Run `python -c "import cv2; cap=cv2.VideoCapture(0); print(cap.isOpened())"` to test independently.

### Low frame rate

- Reduce `ASCII_COLS` (e.g. `80`) in `config.py` — fewer characters = less rendering work.
- Increase `FONT_SIZE` to `10` or `12` — larger glyphs → fewer glyphs to blit.
- Reduce `RAIN_DENSITY` or turn off rain with the `M` key.

### Blurry / distorted image

- Adjust `CONTRAST` (try `1.6`) and `BRIGHTNESS` (try `20`) in `config.py`.
- Use `+` / `-` keys at runtime to find a column count that looks sharp on your screen.

### Missing font (characters look wrong)

The app tries `Consolas`, `Courier New`, `Lucida Console`, and `DejaVu Sans Mono` automatically.  
If none are installed, it falls back to Pygame's built-in bitmap font.  
To force a specific font, set `FONT_NAME = "YourFont"` in `config.py`.

---

## Project Structure

```
matrix_camera/
├── main.py            # App entry point, main loop, event handling
├── camera.py          # Webcam init, frame capture, cleanup
├── ascii_renderer.py  # Frame → ASCII grid + Pygame rendering + glyph cache
├── matrix_rain.py     # Falling stream generation and animation
├── config.py          # All configurable parameters
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## License

MIT — do whatever you want with it.
