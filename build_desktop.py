# =============================================================================
# build_desktop.py — Windows Standalone Executable Builder (PyInstaller)
# =============================================================================

import os
import subprocess
import sys

def build():
    print("===============================================================")
    print(" BUILDING STANDALONE WINDOWS EXECUTABLE (matrix_camera.exe)")
    print("===============================================================\n")

    # Install pyinstaller if missing
    try:
        import PyInstaller
    except ImportError:
        print("[*] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=MatrixCamera",
        "--add-data=config.py;.",
        "--add-data=ascii_renderer.py;.",
        "--add-data=camera.py;.",
        "--add-data=matrix_rain.py;.",
        "main.py"
    ]

    print("[*] Running command:", " ".join(cmd))
    subprocess.check_call(cmd)

    print("\n===============================================================")
    print(" BUILD SUCCESSFUL!")
    print(" Executable generated in: dist/MatrixCamera/MatrixCamera.exe")
    print("===============================================================\n")

if __name__ == '__main__':
    build()
