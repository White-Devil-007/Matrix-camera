# =============================================================================
# main.py — Application entry point: main loop, event handling, coordination
# =============================================================================

import sys
import os
import datetime

# Dependency check with user-friendly messages
try:
    import pygame
except ImportError:
    sys.exit("[ERROR] pygame is not installed.  Run:  pip install pygame")

try:
    import cv2
except ImportError:
    sys.exit("[ERROR] opencv-python is not installed.  Run:  pip install opencv-python")

try:
    import numpy as np
except ImportError:
    sys.exit("[ERROR] numpy is not installed.  Run:  pip install numpy")

import config
from camera        import Camera
from ascii_renderer import preprocess, frame_to_chars, ASCIIRenderer
from matrix_rain   import MatrixRain


# ---------------------------------------------------------------------------
# Helper — load a monospaced font
# ---------------------------------------------------------------------------

def _load_font(size: int) -> pygame.font.Font:
    """Try several monospaced candidates; fall back to Pygame's default."""
    candidates = [
        config.FONT_NAME,
        "Courier New",
        "Consolas",
        "Lucida Console",
        "DejaVu Sans Mono",
    ]
    for name in candidates:
        if name is None:
            continue
        try:
            f = pygame.font.SysFont(name, size, bold=False)
            return f
        except Exception:
            pass
    return pygame.font.Font(None, size)   # Pygame built-in bitmap font


# ---------------------------------------------------------------------------
# HUD rendering
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pill-shaped toggle switch widget
# ---------------------------------------------------------------------------

def _draw_toggle(surface: pygame.Surface, x: int, y: int,
                 label: str, is_on: bool, font: pygame.font.Font) -> None:
    """
    Draws a labelled pill toggle switch at (x, y).
    ON  → filled green pill, knob on the right.
    OFF → dark outline pill, knob on the left.
    """
    pill_w, pill_h = 36, 16
    knob_r         = pill_h // 2 - 2
    label_surf     = font.render(label, True, config.COLOR_HUD_DIM)
    surface.blit(label_surf, (x, y + (pill_h - label_surf.get_height()) // 2))

    px = x + label_surf.get_width() + 8
    py = y

    # Track (pill outline / fill)
    track_rect = pygame.Rect(px, py, pill_w, pill_h)
    track_col  = (0, 160, 50) if is_on else (0, 50, 15)
    pygame.draw.rect(surface, track_col, track_rect, border_radius=pill_h // 2)
    if not is_on:
        pygame.draw.rect(surface, (0, 100, 30), track_rect,
                         width=1, border_radius=pill_h // 2)

    # Knob
    knob_x = px + pill_w - pill_h // 2 if is_on else px + pill_h // 2
    knob_y = py + pill_h // 2
    knob_col = (200, 255, 180) if is_on else (0, 80, 25)
    pygame.draw.circle(surface, knob_col, (knob_x, knob_y), knob_r)


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

class HUD:
    def __init__(self, font: pygame.font.Font):
        self.font = font

    def render(self, surface: pygame.Surface,
               fps: float,
               cols: int,
               camera_on: bool,
               rain_on: bool,
               silhouette_on: bool,
               invert_on: bool,
               bg_learning_pct: float,
               paused: bool,
               show_help: bool) -> None:

        lh = self.font.get_height() + 2
        x, y = 10, 10

        # Text status lines
        status_lines = [
            f"FPS  {fps:>4.0f}",
            f"COLS {cols}",
        ]
        for line in status_lines:
            surf = self.font.render(line, True, config.COLOR_HUD_DIM)
            surface.blit(surf, (x, y))
            y += lh

        y += 4  # small spacer

        # Toggle switches
        _draw_toggle(surface, x, y,      "CAMERA", camera_on,     self.font)
        y += lh + 4
        _draw_toggle(surface, x, y,      "MATRIX", rain_on,       self.font)
        y += lh + 4
        _draw_toggle(surface, x, y,      "SILHOU", silhouette_on, self.font)
        y += lh + 4
        _draw_toggle(surface, x, y,      "INVERT", invert_on,     self.font)
        y += lh + 8

        # Background-learning progress bar (shown only during MOG2 warmup)
        if silhouette_on and bg_learning_pct < 1.0:
            bar_w = 120
            bar_h = 8
            # Track
            pygame.draw.rect(surface, (0, 40, 10),
                             (x, y, bar_w, bar_h), border_radius=4)
            # Fill — pulses slightly to show it's alive
            fill = max(4, int(bar_w * bg_learning_pct))
            pygame.draw.rect(surface, (0, 180, 60),
                             (x, y, fill, bar_h), border_radius=4)
            y += bar_h + 3
            label = self.font.render(
                f"LEARNING BG {int(bg_learning_pct * 100):>3d}%",
                True, (0, 160, 50)
            )
            surface.blit(label, (x, y))
            y += lh + 4

        if paused:
            ps = self.font.render("\u23f8 PAUSED", True, (200, 200, 0))
            surface.blit(ps, (x, y))
            y += lh

        hint = self.font.render("H = help", True, config.COLOR_HUD_DIM)
        surface.blit(hint, (x, y))

        if show_help:
            self._render_help(surface)

    def _render_help(self, surface: pygame.Surface) -> None:
        help_lines = [
            "─── CONTROLS ───",
            "ESC / Q   Quit",
            "SPACE     Pause / Resume",
            "C         Toggle Camera ASCII",
            "M         Toggle Matrix Rain",
            "V         Toggle Silhouette Mode",
            "I         Toggle Invert / Light BG Mode",
            "R         Reset Rain",
            "F         Toggle Fullscreen",
            "S         Save Screenshot",
            "+ / -     ASCII Resolution ±8",
            "H         Toggle This Help",
        ]
        font   = self.font
        lh     = font.get_height() + 3
        w      = 260
        h      = len(help_lines) * lh + 16
        sx, sy = surface.get_width() - w - 10, 10

        box = pygame.Surface((w, h), pygame.SRCALPHA)
        box.fill((0, 20, 0, 200))
        surface.blit(box, (sx, sy))

        for i, line in enumerate(help_lines):
            col  = config.COLOR_HUD if i > 0 else config.COLOR_ASCII_BRIGHT
            surf = font.render(line, True, col)
            surface.blit(surf, (sx + 8, sy + 8 + i * lh))


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Matrix Camera — Digital Rain")

    # Window
    flags  = pygame.FULLSCREEN if config.FULLSCREEN else pygame.RESIZABLE
    screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), flags)

    clock  = pygame.time.Clock()

    # Fonts
    ascii_font = _load_font(config.FONT_SIZE)
    hud_font   = _load_font(config.HUD_FONT_SIZE)

    char_w = ascii_font.size("W")[0]
    char_h = ascii_font.size("W")[1]

    # Mutable state
    ascii_cols      = config.ASCII_COLS
    camera_on       = True
    rain_on         = config.RAIN_ENABLED
    silhouette_mode = config.SILHOUETTE_MODE
    invert_mode     = config.INVERT_MODE
    paused          = False
    fullscreen      = config.FULLSCREEN
    show_help       = False
    last_frame      = None      # last successfully captured BGR frame

    # Sub-systems
    try:
        cam = Camera(config.CAMERA_INDEX)
    except RuntimeError as e:
        # Show error on screen then exit
        screen.fill(config.COLOR_BG)
        err_font = _load_font(18)
        for i, line in enumerate(str(e).split("\n")):
            surf = err_font.render(line, True, (200, 40, 40))
            screen.blit(surf, (20, 20 + i * 24))
        pygame.display.flip()
        pygame.time.wait(5000)
        pygame.quit()
        return

    ascii_renderer = ASCIIRenderer(ascii_font)
    hud            = HUD(hud_font)

    # Compute initial grid dimensions from window size
    def _grid_dims():
        sw, sh = screen.get_size()
        cols   = ascii_cols
        rows   = max(1, int(sh / char_h))
        return cols, rows

    cols, rows = _grid_dims()
    rain = MatrixRain(ascii_font, cols, rows)

    # Rain overlay surface (RGBA so we can alpha-blend)
    rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    running = True
    fps_val = 0.0

    while running:
        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                key = event.key

                if key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif key == pygame.K_SPACE:
                    paused = not paused

                elif key == pygame.K_c:
                    camera_on = not camera_on

                elif key == pygame.K_m:
                    rain_on = not rain_on

                elif key == pygame.K_v:
                    silhouette_mode = not silhouette_mode

                elif key == pygame.K_i:
                    invert_mode = not invert_mode

                elif key == pygame.K_r:
                    rain.reset()

                elif key == pygame.K_h:
                    show_help = not show_help

                elif key == pygame.K_f:
                    fullscreen = not fullscreen
                    flags = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                    screen = pygame.display.set_mode(
                        (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), flags
                    )
                    rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                    cols, rows = _grid_dims()
                    rain.resize(cols, rows)

                elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    ascii_cols = min(320, ascii_cols + 8)
                    cols, rows = _grid_dims()
                    rain.resize(cols, rows)

                elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    ascii_cols = max(40, ascii_cols - 8)
                    cols, rows = _grid_dims()
                    rain.resize(cols, rows)

                elif key == pygame.K_s:
                    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = os.path.join(os.getcwd(), f"screenshot_{ts}.png")
                    pygame.image.save(screen, path)
                    print(f"[INFO] Screenshot saved → {path}")

            elif event.type == pygame.VIDEORESIZE:
                screen    = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                cols, rows = _grid_dims()
                rain.resize(cols, rows)

        # ── Frame capture ──────────────────────────────────────────────────
        if not paused:
            frame = cam.read()
            if frame is not None:
                last_frame = frame

        # ── Rendering ─────────────────────────────────────────────────────
        screen.fill(config.COLOR_BG)

        sw, sh = screen.get_size()

        if camera_on and last_frame is not None:
            # Preprocess: BGR → normalised float32 grid (inverted if invert_mode is True)
            brightness = preprocess(last_frame, ascii_cols, invert_mode=invert_mode)
            grid_rows, grid_cols = brightness.shape

            # Centre the ASCII art
            art_w = grid_cols * char_w
            art_h = grid_rows * char_h
            ox    = (sw - art_w) // 2
            oy    = (sh - art_h) // 2

            # ── Foreground mask for silhouette mode ───────────────────────
            # Downsample cam.fg_mask to the same (rows, cols) as brightness.
            # Only available after MOG2 has read enough frames (warmup period).
            fg_mask_small = None
            if silhouette_mode and cam.fg_mask is not None:
                fg  = cam.fg_mask                    # uint8 H×W, 255=fg
                fh, fw = fg.shape
                gr, gc = brightness.shape
                ri = np.linspace(0, fh - 1, gr).astype(np.int32)
                ci = np.linspace(0, fw - 1, gc).astype(np.int32)
                fg_small = fg[np.ix_(ri, ci)]        # nearest-neighbour downsample

                # Cheap 3×3 dilation: fills small gaps inside hand/arm silhouette
                pad = np.pad(fg_small, 1, mode='edge')
                fg_small = np.maximum.reduce([
                    pad[:-2, :-2], pad[:-2, 1:-1], pad[:-2, 2:],
                    pad[1:-1, :-2], fg_small,        pad[1:-1, 2:],
                    pad[2:,  :-2], pad[2:,  1:-1], pad[2:,  2:],
                ])
                fg_mask_small = (fg_small > 128).astype(np.float32)

            # Build character grid — silhouette uses mask, normal uses full ramp
            char_grid = frame_to_chars(
                brightness,
                use_matrix_charset=True,
                silhouette_mode=silhouette_mode,
                fg_mask=fg_mask_small,
            )

            # Draw ASCII image
            ascii_renderer.render(
                screen, char_grid, brightness, ox, oy,
                silhouette_mode=silhouette_mode,
            )

        # Matrix rain overlay
        if rain_on:
            rain.update()
            rain_surf.fill((0, 0, 0, 0))   # clear overlay
            # Rain covers the whole window; compute offset so cols align with ASCII
            rain_ox = (sw - ascii_cols * char_w) // 2
            rain_oy = 0
            rain.render(rain_surf, rain_ox, rain_oy)

            # Blit with configurable alpha
            rain_surf.set_alpha(config.RAIN_ALPHA)
            screen.blit(rain_surf, (0, 0))

        # HUD
        if config.SHOW_HUD:
            bg_pct = min(1.0, cam.frames_read / config.BG_WARMUP_FRAMES)
            hud.render(screen, fps_val, ascii_cols,
                       camera_on, rain_on, silhouette_mode, invert_mode,
                       bg_pct, paused, show_help)

        pygame.display.flip()
        clock.tick(config.FPS_TARGET)
        fps_val = clock.get_fps()

    # ── Cleanup ───────────────────────────────────────────────────────────
    cam.release()
    pygame.quit()
    print("[INFO] Application exited cleanly.")


if __name__ == "__main__":
    main()
