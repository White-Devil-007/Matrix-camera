import cv2
import numpy as np
import pygame
import config


# ---------------------------------------------------------------------------
# Glyph cache
# ---------------------------------------------------------------------------

class GlyphCache:
    """
    Pre-renders every printable character at every colour stop into Pygame
    surfaces so we never call font.render() during the hot rendering loop.
    """

    # Three representative green shades used for ASCII brightness mapping
    COLOUR_STOPS = [
        config.COLOR_ASCII_DARK,
        config.COLOR_ASCII_MID,
        config.COLOR_ASCII_BRIGHT,
    ]

    def __init__(self, font: pygame.font.Font):
        self.font       = font
        self.char_w, self.char_h = font.size("W")
        self._cache: dict[tuple, pygame.Surface] = {}
        self._prebuild()

    def _prebuild(self) -> None:
        chars = set(config.ASCII_RAMP + config.MATRIX_CHARSET)
        for colour in self.COLOUR_STOPS:
            for ch in chars:
                self._cache[(ch, colour)] = self.font.render(ch, True, colour)

    def get(self, char: str, colour: tuple) -> pygame.Surface:
        key = (char, colour)
        if key not in self._cache:
            self._cache[key] = self.font.render(char, True, colour)
        return self._cache[key]


# ---------------------------------------------------------------------------
# Frame preprocessor
# ---------------------------------------------------------------------------

def preprocess(frame_bgr: np.ndarray, cols: int, invert_mode: bool = False, use_clahe: bool = True) -> np.ndarray:
    """
    BGR frame → 2-D float32 array of values in [0, 1], sized (rows, cols).
    Uses OpenCV C++ SIMD acceleration for ultra-fast downsampling and CLAHE.
    """
    gray_u8 = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    if use_clahe and config.USE_CLAHE:
        clahe = cv2.createCLAHE(clipLimit=config.CLAHE_CLIP_LIMIT, tileGridSize=(8, 8))
        gray_u8 = clahe.apply(gray_u8)

    gray = gray_u8.astype(np.float32)
    gray = gray * config.CONTRAST + config.BRIGHTNESS
    gray_u8 = np.clip(gray, 0, 255).astype(np.uint8)

    # Downsample using OpenCV C++ INTER_NEAREST (10x faster than Python numpy slicing)
    src_h, src_w = gray_u8.shape
    char_aspect = 2.0   # typical monospaced char height / width ratio
    rows = max(1, int(cols * (src_h / src_w) / char_aspect))

    small_u8 = cv2.resize(gray_u8, (cols, rows), interpolation=cv2.INTER_NEAREST)
    small    = small_u8.astype(np.float32) / 255.0

    if invert_mode:
        # Smart Light-BG Mode:
        # Samples outer border pixels to detect true background wall brightness.
        # Removes light background wall into pitch-black space (0.0) while preserving
        # natural face highlights and dark facial features (eyes/eyebrows/hair).
        h_sm, w_sm = small.shape
        border_mask = np.ones((h_sm, w_sm), dtype=bool)
        border_mask[4:-4, 4:-4] = False
        bg_avg = float(np.mean(small[border_mask])) if np.any(border_mask) else 0.65

        if bg_avg > 0.35:
            bg_cutoff = max(0.20, bg_avg - 0.10)
            bg_mask = small >= bg_cutoff

            norm = np.clip(small / bg_cutoff, 0.0, 1.0)
            subject = 0.18 + np.power(norm, 0.7) * 0.82
            subject[bg_mask] = 0.0
            small = subject
        else:
            small = 1.0 - small

    return small.astype(np.float32)   # [0, 1]


# ---------------------------------------------------------------------------
# ASCII grid builder
# ---------------------------------------------------------------------------

def frame_to_chars(brightness: np.ndarray,
                   use_matrix_charset: bool = False,
                   silhouette_mode: bool = False,
                   fg_mask: np.ndarray | None = None) -> list[list[str]]:
    """
    Maps a (rows, cols) brightness array → 2-D list of characters.

    Normal mode:
      Full brightness ramp — dark → sparse chars, bright → dense chars.

    Silhouette mode (mask available — MOG2 background subtractor is ready):
      fg_mask (float32, 1=foreground) decides which pixels are visible.
      Background pixels become spaces regardless of their brightness, so
      hands/body are always separated from the bg even at similar brightness.

    Silhouette mode (mask absent — warmup period, first ~BG_WARMUP_FRAMES frames):
      Falls back to a per-frame Otsu adaptive threshold so the screen isn't
      blank while MOG2 is still learning.
    """
    ramp = config.ASCII_RAMP
    if use_matrix_charset:
        ramp = config.MATRIX_CHARSET

    ramp_len = len(ramp)

    if silhouette_mode:
        # Build a foreground boolean mask ─────────────────────────────────────
        if fg_mask is not None:
            # MOG2 mask: straightforward threshold at 0.5
            is_fg = fg_mask > 0.5
        else:
            # Otsu adaptive fallback: find the natural bimodal split in this frame
            hist, _ = np.histogram(brightness, bins=256, range=(0.0, 1.0))
            total   = brightness.size
            best_var, best_t = 0.0, config.SILHOUETTE_THRESHOLD
            w0 = sum_bg = 0.0
            for t in range(256):
                w0 += hist[t]
                if w0 == 0:
                    continue
                w1 = total - w0
                if w1 == 0:
                    break
                sum_bg += t * hist[t]
                mu0 = sum_bg / w0
                mu1 = (np.sum(np.arange(t + 1, 256) * hist[t + 1:]) / w1) if w1 > 0 else 0
                var = (w0 * w1 * (mu0 - mu1) ** 2)
                if var > best_var:
                    best_var, best_t = var, t / 255.0
            is_fg = brightness >= best_t

        # Build char indices from brightness across the full ramp for rich detail
        indices = (brightness * (ramp_len - 1)).astype(np.int32)
        indices = np.clip(indices, 0, ramp_len - 1)

        rows, cols = indices.shape
        grid = []
        for r in range(rows):
            row_chars = []
            for c in range(cols):
                if is_fg[r, c]:
                    row_chars.append(ramp[indices[r, c]])
                else:
                    row_chars.append(" ")   # background → invisible
            grid.append(row_chars)
        return grid

    # --- Normal mode ---
    indices = (brightness * (ramp_len - 1)).astype(np.int32)
    indices = np.clip(indices, 0, ramp_len - 1)

    rows, cols = indices.shape
    grid = []
    for r in range(rows):
        row_chars = [ramp[indices[r, c]] for c in range(cols)]
        grid.append(row_chars)
    return grid


# ---------------------------------------------------------------------------
# Pygame renderer
# ---------------------------------------------------------------------------

class ASCIIRenderer:
    """
    Renders a character grid onto a Pygame surface using the glyph cache.
    """

    def __init__(self, font: pygame.font.Font):
        self.cache  = GlyphCache(font)
        self.char_w = self.cache.char_w
        self.char_h = self.cache.char_h

    def render(self,
               surface: pygame.Surface,
               grid: list[list[str]],
               brightness: np.ndarray,
               offset_x: int = 0,
               offset_y: int = 0,
               silhouette_mode: bool = False) -> None:
        """
        Blits character grid onto surface using C-level Pygame SDL batch blitting
        for maximum frame rates (MAX FPS MODE).
        """
        stops  = GlyphCache.COLOUR_STOPS
        cw, ch = self.char_w, self.char_h
        sw, sh = surface.get_width(), surface.get_height()
        b_rows, b_cols = brightness.shape

        if config.USE_FAST_BLIT:
            blits = []
            for r, row in enumerate(grid):
                y = offset_y + r * ch
                if y > sh:
                    break
                for c, char in enumerate(row):
                    if char == " ":
                        continue
                    x = offset_x + c * cw
                    if x > sw:
                        break

                    val = float(brightness[r, c]) if r < b_rows and c < b_cols else 0.0
                    colour = stops[0] if val < 0.33 else (stops[1] if val < 0.67 else stops[2])
                    glyph = self.cache.get(char, colour)
                    blits.append((glyph, (x, y)))

            if blits:
                surface.blits(blits)
        else:
            for r, row in enumerate(grid):
                y = offset_y + r * ch
                if y > sh:
                    break
                for c, char in enumerate(row):
                    if char == " ":
                        continue
                    x = offset_x + c * cw
                    if x > sw:
                        break

                    val = float(brightness[r, c]) if r < b_rows and c < b_cols else 0.0
                    colour = stops[0] if val < 0.33 else (stops[1] if val < 0.67 else stops[2])
                    glyph = self.cache.get(char, colour)
                    surface.blit(glyph, (x, y))

    def grid_pixel_size(self, cols: int, rows: int) -> tuple[int, int]:
        return cols * self.char_w, rows * self.char_h
