/* =============================================================================
   app.js — Real-Time Web & Mobile Matrix Camera Engine (JavaScript + HTML5 Canvas)
   Matches Python main.py high-density ASCII resolution & quality!
   ============================================================================= */

class MatrixCameraApp {
  constructor() {
    this.video = document.getElementById('webcam');
    this.procCanvas = document.getElementById('procCanvas');
    this.procCtx = this.procCanvas.getContext('2d', { willReadFrequently: true });
    this.outCanvas = document.getElementById('outputCanvas');
    this.outCtx = this.outCanvas.getContext('2d');

    /* =========================================================================
       PROGRAM CONFIGURATION SETTINGS (Tweak these values to alter the output!)
       ========================================================================= */

    // 1. ASCII CAMERA RESOLUTION & DETAIL
    this.cols = 410;             // Number of ASCII columns across screen width.
                                 // Higher (400-600) = Fine detail / sharp facial features.
                                 // Lower (100-200) = Large blocky characters.

    // 2. IMAGE PREPROCESSING & CONTRAST
    this.contrast = 1.35;        // Contrast multiplier (1.0 = normal, 1.35 = punchy highlights).
    this.brightness = 0.03;      // Brightness offset (adds subtle base glow to dark regions).
    this.asciiRamp = " .:-=+*#%@"; // Character ramp mapped from dark (left) to bright (right).

    // 3. COLOR PALETTE (Pygame RGB Stops)
    this.colorDark = "rgb(0, 80, 0)";        // Low brightness pixels (dark contours/hair)
    this.colorMid = "rgb(0, 180, 40)";       // Midtone skin & facial highlights
    this.colorBright = "rgba(0, 217, 255, 1)";  // Vivid highlights & intense spots

    // 4. MATRIX DIGITAL RAIN (Background Rain Streams)
    this.rainEnabled = true;     // Master toggle for Matrix rain effect.
    this.rainDensity = 0.75;     // Percentage of screen columns with active rain (0.25 = 25% density, smaller & fewer).
    this.rainFontSize = 11;      // Pixel height of rain characters (smaller = subtle background code).
    this.rainMinSpeed = 2;       // Minimum fall speed (pixels per frame).
    this.rainMaxSpeed = 5;       // Maximum fall speed (pixels per frame).
    this.rainMinLength = 5;      // Minimum drop length in characters.
    this.rainMaxLength = 12;     // Maximum drop length in characters.

    // 5. INVERT MODE (Smart Light-BG Suppression)
    this.invertCutoffPct = 0.78; // Cutoff percentile (78%) for isolating light background walls into pitch-black.

    // 6. INITIAL TOGGLES & CAMERA MODES
    this.cameraEnabled = true;   // Live camera feed ON/OFF
    this.invertMode = false;     // Smart Light-BG Invert Mode ON/OFF
    this.silhouetteMode = false; // Silhouette motion-only mode ON/OFF
    this.facingMode = 'user';    // 'user' (front selfie camera) or 'environment' (rear camera)

    /* =========================================================================
       END OF CONFIGURATION SETTINGS
       ========================================================================= */

    // Rain overlay streams & background model
    this.rainStreams = [];
    this.bgModel = null;
    this.frameCount = 0;

    // Performance Stats
    this.lastTime = performance.now();
    this.fps = 0;
    this.frameCountFps = 0;

    this.init();
  }

  async init() {
    document.getElementById('fpsDisplay').innerText = `FPS: -- | COLS: ${this.cols}`;
    this.bindEvents();
    await this.startCamera();
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
    requestAnimationFrame((t) => this.loop(t));
  }

  async startCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }

    try {
      const constraints = {
        video: {
          facingMode: this.facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      this.video.srcObject = this.stream;
      await this.video.play();
    } catch (err) {
      console.error("Camera access error:", err);
      alert("Unable to access camera: " + err.message);
    }
  }

  resizeCanvas() {
    this.outCanvas.width = window.innerWidth;
    this.outCanvas.height = window.innerHeight;
    this.initRain();
  }

  initRain() {
    const fontH = this.rainFontSize;
    const fontW = Math.floor(fontH * 0.65);
    const totalCols = Math.floor(this.outCanvas.width / fontW);
    
    this.rainStreams = [];
    for (let c = 0; c < totalCols; c++) {
      // Spawn rain streams on only a fraction of columns (based on rainDensity)
      if (Math.random() > this.rainDensity) continue;

      this.rainStreams.push({
        x: c * fontW,
        y: Math.random() * -this.outCanvas.height,
        speed: this.rainMinSpeed + Math.random() * (this.rainMaxSpeed - this.rainMinSpeed),
        length: this.rainMinLength + Math.floor(Math.random() * (this.rainMaxLength - this.rainMinLength))
      });
    }
  }

  bindEvents() {
    // HUD Control Buttons
    document.getElementById('btnToggleCam').addEventListener('click', (e) => {
      this.cameraEnabled = !this.cameraEnabled;
      e.currentTarget.classList.toggle('active', this.cameraEnabled);
    });

    document.getElementById('btnToggleRain').addEventListener('click', (e) => {
      this.rainEnabled = !this.rainEnabled;
      e.currentTarget.classList.toggle('active', this.rainEnabled);
    });

    document.getElementById('btnToggleInvert').addEventListener('click', (e) => {
      this.invertMode = !this.invertMode;
      e.currentTarget.classList.toggle('active', this.invertMode);
    });

    document.getElementById('btnToggleSilhou').addEventListener('click', (e) => {
      this.silhouetteMode = !this.silhouetteMode;
      e.currentTarget.classList.toggle('active', this.silhouetteMode);
    });

    document.getElementById('btnFlipCam').addEventListener('click', () => {
      this.facingMode = (this.facingMode === 'user') ? 'environment' : 'user';
      this.startCamera();
    });

    document.getElementById('btnSnap').addEventListener('click', () => this.takeScreenshot());

    document.getElementById('btnFullscreen').addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      const key = e.key.toUpperCase();
      if (key === 'I') document.getElementById('btnToggleInvert').click();
      if (key === 'V') document.getElementById('btnToggleSilhou').click();
      if (key === 'M') document.getElementById('btnToggleRain').click();
      if (key === 'C') document.getElementById('btnToggleCam').click();
      if (key === '+') { this.cols = Math.min(600, this.cols + 50); this.initRain(); }
      if (key === '-') { this.cols = Math.max(80, this.cols - 50); this.initRain(); }
    });
  }

  takeScreenshot() {
    const link = document.createElement('a');
    link.download = `matrix_camera_${Date.now()}.png`;
    link.href = this.outCanvas.toDataURL('image/png');
    link.click();
  }

  loop(now) {
    this.frameCount++;
    this.frameCountFps++;

    if (now - this.lastTime >= 1000) {
      this.fps = this.frameCountFps;
      this.frameCountFps = 0;
      this.lastTime = now;
      document.getElementById('fpsDisplay').innerText = `FPS: ${this.fps} | COLS: ${this.cols}`;
    }

    // Clear Screen to Pitch Black
    this.outCtx.fillStyle = '#000000';
    this.outCtx.fillRect(0, 0, this.outCanvas.width, this.outCanvas.height);

    if (this.cameraEnabled && this.video.readyState === 4) {
      this.renderASCII();
    }

    if (this.rainEnabled) {
      this.renderRain();
    }

    requestAnimationFrame((t) => this.loop(t));
  }

  renderASCII() {
    const charAspect = 2.0; // Monospaced aspect ratio matching Python char_aspect = 2.0
    const vW = this.video.videoWidth || 640;
    const vH = this.video.videoHeight || 480;

    // Calculate grid rows preserving camera aspect ratio (matches Python preprocess)
    const rows = Math.max(1, Math.floor((this.cols * (vH / vW)) / charAspect));
    
    this.procCanvas.width = this.cols;
    this.procCanvas.height = rows;

    // Draw video frame to small canvas
    if (this.facingMode === 'user') {
      this.procCtx.save();
      this.procCtx.scale(-1, 1);
      this.procCtx.drawImage(this.video, -this.cols, 0, this.cols, rows);
      this.procCtx.restore();
    } else {
      this.procCtx.drawImage(this.video, 0, 0, this.cols, rows);
    }

    const imgData = this.procCtx.getImageData(0, 0, this.cols, rows);
    const data = imgData.data;

    // Font and Cell Sizing to fit screen aspect ratio
    const scaleX = this.outCanvas.width / this.cols;
    const scaleY = this.outCanvas.height / rows;
    const fontW = Math.min(scaleX, scaleY / charAspect);
    const fontH = fontW * charAspect;
    const fontPx = Math.max(4, Math.floor(fontH));

    this.outCtx.font = `700 ${fontPx}px 'Fira Code', 'Courier New', monospace`;
    this.outCtx.textBaseline = 'top';

    const brightnessGrid = new Float32Array(this.cols * rows);
    const totalPixels = this.cols * rows;

    // Grayscale Luminance + Contrast Adjustment (matches Python config.CONTRAST & BRIGHTNESS)
    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      let lum = (0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2]) / 255.0;
      lum = lum * this.contrast + this.brightness;
      brightnessGrid[i] = Math.min(1.0, Math.max(0.0, lum));
    }

    // Smart Light-BG Invert Mode
    if (this.invertMode) {
      const sorted = Float32Array.from(brightnessGrid).sort();
      const pBg = sorted[Math.floor(totalPixels * this.invertCutoffPct)];
      const pFgMin = sorted[Math.floor(totalPixels * 0.05)];

      if (pBg - pFgMin > 0.05) {
        const bgCutoff = pBg - 0.02;
        const range = Math.max(0.01, bgCutoff - pFgMin);

        for (let i = 0; i < totalPixels; i++) {
          const val = brightnessGrid[i];
          if (val >= bgCutoff) {
            brightnessGrid[i] = 0.0; // Black background space
          } else {
            const norm = Math.min(1.0, Math.max(0.0, (val - pFgMin) / range));
            brightnessGrid[i] = 0.15 + norm * 0.85; // Glowing skin, dark contours
          }
        }
      } else {
        for (let i = 0; i < totalPixels; i++) {
          brightnessGrid[i] = 1.0 - brightnessGrid[i];
        }
      }
    }

    // Silhouette Mode (Background Subtraction)
    if (this.silhouetteMode) {
      if (!this.bgModel) {
        this.bgModel = Float32Array.from(brightnessGrid);
      } else {
        const alpha = 0.05;
        for (let i = 0; i < totalPixels; i++) {
          const diff = Math.abs(brightnessGrid[i] - this.bgModel[i]);
          if (diff <= 0.18) {
            this.bgModel[i] = this.bgModel[i] * (1 - alpha) + brightnessGrid[i] * alpha;
            brightnessGrid[i] = 0.0;
          }
        }
      }
    }

    // Render ASCII Characters with Python-exact color stops
    const rampLen = this.asciiRamp.length;
    const gridW = this.cols * fontW;
    const gridH = rows * fontH;
    const startX = (this.outCanvas.width - gridW) / 2;
    const startY = (this.outCanvas.height - gridH) / 2;

    for (let r = 0; r < rows; r++) {
      const y = startY + r * fontH;
      if (y < -fontH || y > this.outCanvas.height) continue;

      for (let c = 0; c < this.cols; c++) {
        const val = brightnessGrid[r * this.cols + c];
        if (val < 0.05) continue;

        const charIdx = Math.min(rampLen - 1, Math.floor(val * rampLen));
        const ch = this.asciiRamp[charIdx];

        if (val < 0.33) {
          this.outCtx.fillStyle = this.colorDark;      // (0, 80, 0)
        } else if (val < 0.67) {
          this.outCtx.fillStyle = this.colorMid;       // (0, 180, 40)
        } else {
          this.outCtx.fillStyle = this.colorBright;    // (140, 255, 100)
        }

        const x = startX + c * fontW;
        this.outCtx.fillText(ch, x, y);
      }
    }
  }

  renderRain() {
    const fontH = this.rainFontSize;
    this.outCtx.font = `600 ${fontH}px 'Fira Code', 'Courier New', monospace`;

    for (let s of this.rainStreams) {
      s.y += s.speed;
      if (s.y > this.outCanvas.height + s.length * fontH) {
        s.y = -s.length * fontH;
        s.speed = this.rainMinSpeed + Math.random() * (this.rainMaxSpeed - this.rainMinSpeed);
      }

      for (let i = 0; i < s.length; i++) {
        const charY = s.y - i * fontH;
        if (charY < 0 || charY > this.outCanvas.height) continue;

        const charCode = 0x30A0 + Math.floor(Math.random() * 96); // Matrix Katakana & ASCII
        const ch = String.fromCharCode(charCode);

        if (i === 0) {
          this.outCtx.fillStyle = '#ffffff'; // Leading bright head character
        } else if (i < 3) {
          this.outCtx.fillStyle = '#8cff64';
        } else {
          this.outCtx.fillStyle = `rgba(0, 180, 40, ${0.8 - (i / s.length) * 0.7})`;
        }

        this.outCtx.fillText(ch, s.x, charY);
      }
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.app = new MatrixCameraApp();
});
