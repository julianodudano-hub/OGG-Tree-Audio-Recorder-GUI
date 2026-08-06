# OGG Tree Audio Recorder GUI

**OGG Tree Audio Recorder GUI** is a Python-based application for Windows and Linux designed to browse, preview, and re-record/replace `.ogg` audio files within complex, nested directory structures.

The application automatically mirrors the input directory tree to the output path, allowing you to quickly process files one by one without manually recreating subfolders or navigating file explorers.

---

## 🎯 Purpose & Use Cases

This tool was built to automate and speed up audio workflows that require mass file replacement across deep directory structures.

### Key Use Cases:
* **Game Localization & Voice Over:** Ideal for voice actors and dubbing teams re-recording dialogue lines (which games often store across dozens of nested folders as `.ogg` files).
* **Audio Modding:** Rapidly replacing sound effects, music, or dialogue in games and software applications.
* **Batch Sample Recording:** Recording against a structured list of audio assets without the risk of misnaming files or saving them to the wrong directory.

---

## ✨ Key Features

- **Automatic Directory Tree Mirroring:**
  Scans the entire input directory and automatically recreates the identical subfolder structure in the destination path when saving recorded files.

- **Natural File Sorting (`Natural Sort`):**
  Sorts files and folders intuitively (e.g., `file1.ogg`, `file2.ogg`, `file10.ogg`) instead of standard alphabetical order (where `file10.ogg` appears before `file2.ogg`).

- **Dual Audio Player (Comparative Listening):**
  * Listen to the **original source track**.
  * Preview your **newly recorded track** before moving to the next file.

- **Built-in Audio Recorder:**
  * Direct capture from the default microphone at 44.1 kHz Stereo.
  * Real-time buffer encoding natively saved to OGG Vorbis format.
  * Configurable maximum recording duration with an active UI countdown.
  * One-click manual recording termination.

- **Modern GUI Design:**
  * Clean Dark Mode interface built with `CustomTkinter`.
  * Multithreaded execution prevents UI freezing during recording and playback.
  * Simple navigation controls (*Previous*, *Next*, *Reset Recording*).

---

## 🔄 Workflow Overview

1. **Select Paths:** Choose your Source Folder (containing original `.ogg` files) and Destination Folder (where new recordings will be saved).
2. **Scan Structure:** The program indexes all `.ogg` files and sets the queue pointer to the first file (e.g., `File [1/45]`).
3. **Listen & Record:**
   * Click **Play Original** to review the target audio line/effect.
   * Click **Record** to capture your new version from the microphone.
   * Optionally click **Play Recording** to verify your take.
4. **Auto-Save:** Once recorded, the file is automatically saved into the mirrored subfolder path under its original name.
5. **Navigate:** Click **Next** to proceed to the next file in the tree.

---

## 🛠️ Technical Requirements

Running the application requires **Python 3.10+** and the following packages:

* **CustomTkinter** – GUI framework
* **Pygame** – Audio playback engine (SDL2)
* **SoundDevice** – Microphone audio capture
* **SoundFile** – OGG Vorbis I/O encoding
* **NumPy** – Audio buffer processing
