# Matrix Digital Rain Camera — Hosting & Deployment Guide

This guide provides step-by-step instructions on how to run, host, and deploy the Matrix Camera application on **Windows Desktop Browsers**, **Mobile Browsers (iOS Safari / Android Chrome)**, and how to package standalone desktop binaries.

---

## 1. Overview of Modes

| Mode | Platform | Engine | Primary Command / URL |
|------|----------|--------|-----------------------|
| **Python Desktop App** | Windows / macOS / Linux | Pygame + OpenCV | `python main.py` |
| **Local Web / Mobile** | Windows Browser + Smartphone | HTML5 Canvas + WebRTC | `python server.py` |
| **Cloud Deployed App** | iOS / Android / Any Browser | Web PWA | Vercel / Netlify / GitHub Pages |
| **Standalone Executable** | Windows Desktop (.exe) | PyInstaller | `python build_desktop.py` |

---

## 2. How to Run on a Windows Desktop Browser

### Method A: Using the Included Local Server (`server.py`)
1. Open terminal in the `matrix_camera` directory.
2. Run:
   ```bash
   python server.py
   ```
3. Your default web browser will automatically open to `http://localhost:8000`.
4. Allow browser permission for camera access when prompted.

### Method B: Using Python's Native HTTP Module
```bash
cd web
python -m http.server 8000
```
Open `http://localhost:8000` in Chrome, Edge, Brave, or Firefox.

### Windows Browser Controls & Shortcuts:
* **`I`**: Toggle **Smart Light-BG Invert Mode** (removes white walls into dark space, keeps natural skin & facial details).
* **`V`**: Toggle **Silhouette Mode** (motion-based background subtraction).
* **`M`**: Toggle **Matrix Digital Rain** streams overlay.
* **`C`**: Toggle Webcam ASCII feed.
* **`+` / `-`**: Increase / decrease character resolution columns.
* **`F`**: Toggle Fullscreen mode.

---

## 3. How to Run on a Mobile Browser (iPhone / Android)

### Method A: Local Wi-Fi Connection (Zero Cloud Setup)
1. Ensure your PC and mobile phone are connected to the **same Wi-Fi network**.
2. On your PC, open a terminal in `matrix_camera` and run:
   ```bash
   python server.py
   ```
3. Look at the terminal output for your **Mobile / Wi-Fi URL**:
   ```
   [*] Mobile / Wi-Fi URL: http://192.168.X.X:8000
   ```
4. On your **iPhone (Safari)** or **Android (Chrome)**, open that URL (`http://192.168.X.X:8000`).
5. Tap **Allow** when requested for camera access.

### Method B: Install as a Native Mobile App (PWA)
1. Open the app URL in Safari (iOS) or Chrome (Android).
2. **iOS Safari**: Tap the **Share** button at the bottom -> Tap **"Add to Home Screen"**.
3. **Android Chrome**: Tap the **Three Dots (Menu)** top-right -> Tap **"Add to Home Screen"** / **"Install App"**.
4. The app icon will appear on your phone home screen and open in full-screen native mode!

### Mobile Browser Features:
* **FLIP Button**: Switch between **Front (Selfie) Camera** and **Rear (Back) Camera**.
* **Touch Bar**: Tap HUD toggle pills (**CAM**, **RAIN**, **INVERT**, **SILHOU**) for real-time adjustments.
* **Save Snapshot**: Tap the Camera Icon button to save high-resolution Matrix PNG images to your photo gallery.

---

## 4. How to Host and Deploy Online (Free Cloud Hosting)

> [!IMPORTANT]
> **HTTPS Camera Access Requirement**: Modern mobile browsers (iOS Safari & Android Chrome) **require an HTTPS connection** to access camera hardware over public domains. Hosting on Vercel, Netlify, or GitHub Pages automatically provides free SSL/HTTPS certificates.

### Deployment Option 1: Vercel (Recommended — 1-Click)
1. Install Vercel CLI (optional) or upload via GitHub:
   ```bash
   npm i -g vercel
   vercel
   ```
2. Set root directory to `./` (the repository root contains `vercel.json` and `web/`).
3. Vercel will generate a production HTTPS URL (e.g. `https://matrix-camera.vercel.app`).

### Deployment Option 2: Netlify (Drag & Drop)
1. Go to [Netlify Drop](https://app.netlify.com/drop).
2. Drag and drop the **`web/`** folder directly into the browser upload box.
3. Netlify instantly generates a live HTTPS URL.

### Deployment Option 3: GitHub Pages
1. Push the repository to GitHub.
2. Go to **Repository Settings** -> **Pages**.
3. Select **Source**: `Deploy from a branch`.
4. Choose `main` branch and folder `/web`.
5. Save. Your app will be live at `https://<username>.github.io/<repo-name>/`.

---

## 5. How to Package a Standalone Windows `.exe`

To generate an executable that runs on any Windows PC without Python:

1. Open terminal in `matrix_camera` and run:
   ```bash
   python build_desktop.py
   ```
2. PyInstaller will compile the app and place the output in:
   ```
   dist/MatrixCamera/MatrixCamera.exe
   ```
3. You can copy or zip the `dist/MatrixCamera` folder and run `MatrixCamera.exe` on any Windows computer.

---

## 6. Project File Structure Reference

```
matrix_camera/
├── web/                        # Web & Mobile Application
│   ├── index.html              # Responsive HTML5 UI & PWA Layout
│   ├── style.css               # Matrix Dark Cyberpunk Styles
│   ├── app.js                  # JavaScript WebGL/Canvas Matrix ASCII Engine
│   ├── manifest.json           # Mobile PWA Manifest
│   └── sw.js                   # Service Worker for Offline Mobile Support
├── server.py                   # Local Cross-Device Web Server Launcher
├── build_desktop.py            # Windows Standalone Executable Builder
├── main.py                     # Desktop Python Application Entrypoint
├── config.py                   # Centralized Configuration & Settings
├── camera.py                   # OpenCV Camera Feed & MOG2 Background Subtractor
├── ascii_renderer.py           # Python ASCII Processor & CLAHE Contrast Engine
├── matrix_rain.py              # Python Matrix Rain Generator
├── requirements.txt            # Python Dependencies
├── vercel.json                 # Vercel Deployment Configuration
└── instruction.md              # This Hosting & Deployment Guide
```
