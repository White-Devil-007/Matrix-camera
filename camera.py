# =============================================================================
# camera.py — Webcam initialisation, frame capture, and cleanup
# =============================================================================

import cv2
import numpy as np
import config


class Camera:
    """Wraps an OpenCV VideoCapture, providing mirrored frame reads."""

    def __init__(self, index: int = config.CAMERA_INDEX):
        self.index       = index
        self.cap         = None
        self.fg_mask     = None   # uint8 H×W — 255=foreground, 0=background
        self.frames_read = 0      # incremented on every successful read

        # MOG2 learns the static background; any new object (hand, person)
        # is flagged as foreground regardless of its brightness.
        self._bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=config.BG_WARMUP_FRAMES,
            varThreshold=40,
            detectShadows=False,
        )
        self._open()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _open(self) -> None:
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)  # CAP_DSHOW = faster on Windows
        if not self.cap.isOpened():
            # Try again without the backend hint (cross-platform fallback)
            self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Cannot open webcam (index={self.index}).\n"
                "Possible causes:\n"
                "  • No webcam connected or recognised.\n"
                "  • Another application has exclusive access to the camera.\n"
                "  • Insufficient permissions (check OS privacy settings).\n"
                "  • Wrong CAMERA_INDEX in config.py."
            )
        # Request a reasonable capture resolution — driver may choose nearest supported
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # ------------------------------------------------------------------
    # Frame access
    # ------------------------------------------------------------------

    def read(self) -> np.ndarray | None:
        """
        Returns the latest BGR frame, or None if capture failed.
        Applies horizontal mirror when config.MIRROR_CAMERA is True.
        """
        if self.cap is None or not self.cap.isOpened():
            return None

        ok, frame = self.cap.read()
        if not ok or frame is None:
            return None

        if config.MIRROR_CAMERA:
            frame = cv2.flip(frame, 1)

        # Update background model and store the foreground mask.
        # Applied after mirroring so the mask stays spatially aligned with the frame.
        self.fg_mask = self._bg_sub.apply(frame)
        self.frames_read += 1

        return frame

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.release()
