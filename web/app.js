/* =============================================================================
   app.js — Real-Time Web & Mobile Matrix Camera Engine (JavaScript + HTML5 Canvas)
   ============================================================================= */

class MatrixCameraApp {
  constructor() {
    this.video = document.getElementById('webcam');
    this.procCanvas = document.getElementById('procCanvas');
    this.procCtx = this.procCanvas.getContext('2d', { willReadFrequently: true });
    this.outCanvas = document.getElementById('outputCanvas');
    this.outCtx = this.outCanvas.getContext('2d');

    // Configuration & State
    this.cols = 160;
    this.cameraEnabled = true;
    this.rainEnabled = true;
    this.invertMode = false;
    this.silhouetteMode = false;
    this.facingMode = 'user'; // 'user' or 'environment' for mobile flip

    // ASCII Ramp & Colors
    this.asciiRamp = " .:-=+*#%@";
    this.colorDark = "#005000";
    this.colorMid = "#00b428";
    this.colorBright = "#8cff64";

    // Rain overlay streams
    this.rainStreams = [];
    
    // Background Subtraction for Silhouette Mode
    this.bgModel = null;
    this.frameCount = 0;

    // Performance Stats
    this.lastTime = performance.now();
    this.fps = 0;
    this.frameCountFps = 0;

    this.init();
  }

  async init() {
    this.bindEvents();
    await this.startCamera();
    this.initRain();
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
    const fontHeight = Math.max(6, Math.floor(this.outCanvas.width / this.cols * 1.8));
    const fontWidth = Math.floor(fontHeight / 1.8);
    const rainCols = Math.floor(this.outCanvas.width / fontWidth);
    
    this.rainStreams = [];
    for (let c = 0; c < rainCols; c++) {
      this.rainStreams.push({
        x: c * fontWidth,
        y: Math.random() * -this.outCanvas.height,
        speed: 2 + Math.random() * 5,
        length: 8 + Math.floor(Math.random() * 20),
        chars: []
      });
    }
  }

  bindEvents() {
    // Buttons
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
      if (key === '+') { this.cols = Math.min(400, this.cols + 20); this.initRain(); }
      if (key === '-') { this.cols = Math.max(40, this.cols - 20); this.initRain(); }
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

    // Clear Screen
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
    const charAspect = 1.8;
    const vW = this.video.videoWidth || 640;
    const vH = this.video.videoHeight || 480;

    const rows = Math.floor((this.cols * (vH / vW)) / charAspect);
    
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

    // Font sizing
    const fontW = this.outCanvas.width / this.cols;
    const fontH = fontW * charAspect;
    const fontPx = Math.floor(fontH);

    this.outCtx.font = `700 ${fontPx}px 'Fira Code', monospace`;
    this.outCtx.textBaseline = 'top';

    const brightnessGrid = new Float32Array(this.cols * rows);
    const totalPixels = this.cols * rows;

    // Grayscale Luminance
    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      const lum = (0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2]) / 255.0;
      brightnessGrid[i] = lum;
    }

    // Smart Light-BG Invert Mode
    if (this.invertMode) {
      // Calculate 80th percentile for background wall isolation
      const sorted = Float32Array.from(brightnessGrid).sort();
      const pBg = sorted[Math.floor(totalPixels * 0.78)];
      const pFgMin = sorted[Math.floor(totalPixels * 0.05)];

      if (pBg - pFgMin > 0.05) {
        const bgCutoff = pBg - 0.02;
        const range = Math.max(0.01, bgCutoff - pFgMin);

        for (let i = 0; i < totalPixels; i++) {
          const val = brightnessGrid[i];
          if (val >= bgCutoff) {
            brightnessGrid[i] = 0.0; // Black background
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
        // Simple running background learning
        const alpha = 0.05;
        for (let i = 0; i < totalPixels; i++) {
          const diff = Math.abs(brightnessGrid[i] - this.bgModel[i]);
          if (diff > 0.18) {
            // Foreground object detected!
          } else {
            // Background update & suppress
            this.bgModel[i] = this.bgModel[i] * (1 - alpha) + brightnessGrid[i] * alpha;
            brightnessGrid[i] = 0.0;
          }
        }
      }
    }

    // Render ASCII Characters
    const rampLen = this.asciiRamp.length;
    const startX = (this.outCanvas.width - this.cols * fontW) / 2;
    const startY = (this.outCanvas.height - rows * fontH) / 2;

    for (let r = 0; r < rows; r++) {
      const y = startY + r * fontH;
      if (y < -fontH || y > this.outCanvas.height) continue;

      for (let c = 0; c < this.cols; c++) {
        const val = brightnessGrid[r * this.cols + c];
        if (val < 0.05) continue;

        const charIdx = Math.min(rampLen - 1, Math.floor(val * rampLen));
        const ch = this.asciiRamp[charIdx];

        if (val < 0.33) {
          this.outCtx.fillStyle = this.colorDark;
        } else if (val < 0.67) {
          this.outCtx.fillStyle = this.colorMid;
        } else {
          this.outCtx.fillStyle = this.colorBright;
        }

        const x = startX + c * fontW;
        this.outCtx.fillText(ch, x, y);
      }
    }
  }

  renderRain() {
    const fontH = 14;
    this.outCtx.font = `600 ${fontH}px 'Fira Code', monospace`;

    for (let s of this.rainStreams) {
      s.y += s.speed;
      if (s.y > this.outCanvas.height + s.length * fontH) {
        s.y = -s.length * fontH;
        s.speed = 2 + Math.random() * 5;
      }

      for (let i = 0; i < s.length; i++) {
        const charY = s.y - i * fontH;
        if (charY < 0 || charY > this.outCanvas.height) continue;

        const charCode = 0x30A0 + Math.floor(Math.random() * 96); // Matrix Katakana & ASCII
        const ch = String.fromCharCode(charCode);

        if (i === 0) {
          this.outCtx.fillStyle = '#ffffff'; // Leading bright head
        } else if (i < 3) {
          this.outCtx.fillStyle = '#8cff64';
        } else {
          this.outCtx.fillStyle = `rgba(0, 180, 40, ${1 - i / s.length})`;
        }

        this.outCtx.fillText(ch, s.x, charY);
      }
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.app = new MatrixCameraApp();
});
