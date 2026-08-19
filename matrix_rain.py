# =============================================================================
# matrix_rain.py — Falling Matrix digital-rain streams
# =============================================================================

import random
import pygame
import config


# ---------------------------------------------------------------------------
# Single stream
# ---------------------------------------------------------------------------

class Stream:
    """Represents one vertical column of falling characters."""

    def __init__(self, col: int, total_rows: int):
        self.col        = col
        self.total_rows = total_rows
        self._spawn()

    def _spawn(self) -> None:
        self.head    = random.randint(-config.RAIN_LENGTH_MAX, 0)
        self.length  = random.randint(config.RAIN_LENGTH_MIN, config.RAIN_LENGTH_MAX)
        self.speed   = random.randint(config.RAIN_SPEED_MIN,  config.RAIN_SPEED_MAX)
        self.chars   = [random.choice(config.MATRIX_CHARSET) for _ in range(self.length)]
        self._tick   = 0

    def update(self) -> None:
        self._tick += 1
        if self._tick >= self.speed:
            self._tick = 0
            self.head += 1
            # Randomly mutate one character per advance for the flicker effect
            idx = random.randrange(self.length)
            self.chars[idx] = random.choice(config.MATRIX_CHARSET)

        if self.head - self.length > self.total_rows:
            self._spawn()

    def visible_cells(self) -> list[tuple[int, int, str, str]]:
        """
        Yields (row, col, char, role) where role is 'head'|'body'|'tail'.
        Only rows inside the grid are returned.
        """
        cells = []
        for i in range(self.length):
            row = self.head - i
            if row < 0 or row >= self.total_rows:
                continue
            char = self.chars[i % len(self.chars)]
            if i == 0:
                role = "head"
            elif i < self.length // 3:
                role = "body"
            else:
                role = "tail"
            cells.append((row, self.col, char, role))
        return cells


# ---------------------------------------------------------------------------
# Rain manager
# ---------------------------------------------------------------------------

class MatrixRain:
    """
    Manages the full set of streams across a character grid and renders them
    onto an RGBA overlay surface so they can be alpha-blended over the ASCII
    camera image.
    """

    ROLE_COLOUR = {
        "head": config.COLOR_RAIN_HEAD,
        "body": config.COLOR_RAIN_BODY,
        "tail": config.COLOR_RAIN_FADE,
    }

    def __init__(self, font: pygame.font.Font, cols: int, rows: int):
        self.font    = font
        self.char_w, self.char_h = font.size("W")
        self.cols    = cols
        self.rows    = rows
        self.streams: list[Stream] = []
        self._build_streams()

    # ------------------------------------------------------------------

    def _build_streams(self) -> None:
        self.streams.clear()
        # Seed some streams immediately so the screen isn't empty at start
        for col in range(self.cols):
            if random.random() < config.RAIN_DENSITY * 5:
                self.streams.append(Stream(col, self.rows))

    def reset(self) -> None:
        self._build_streams()

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self._build_streams()

    # ------------------------------------------------------------------

    def update(self) -> None:
        """Advance all streams and probabilistically spawn new ones."""
        for s in self.streams:
            s.update()

        # Spawn new streams stochastically each frame
        if random.random() < config.RAIN_DENSITY * self.cols:
            col = random.randrange(self.cols)
            self.streams.append(Stream(col, self.rows))

        # Cap total streams to avoid unbounded growth
        max_streams = self.cols * 3
        if len(self.streams) > max_streams:
            self.streams = self.streams[-max_streams:]

    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        """
        Draw rain characters directly onto surface.
        surface should be an RGBA surface for transparency support.
        """
        cw, ch = self.char_w, self.char_h
        render_fn = self.font.render

        for stream in self.streams:
            for row, col, char, role in stream.visible_cells():
                x = offset_x + col * cw
                y = offset_y + row * ch
                colour = self.ROLE_COLOUR[role]
                glyph  = render_fn(char, True, colour)
                surface.blit(glyph, (x, y))
