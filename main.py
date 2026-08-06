import os
import re
import threading
import time
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox

import sounddevice as sd
import soundfile as sf
import pygame

# Inicjalizacja stabilnego silnika odtwarzania SDL2
pygame.mixer.init()

# --- ŁATKA DLA PYTHON 3.13 I CUSTOMTKINTER (Błąd scrollowania myszy) ---
orig_check_scroll = ctk.CTkScrollableFrame._check_if_valid_scroll

def _patched_check_if_valid_scroll(self, widget):
    if isinstance(widget, str):
        try:
            widget = self.nametowidget(widget)
        except Exception:
            return False
    return orig_check_scroll(self, widget)

ctk.CTkScrollableFrame._check_if_valid_scroll = _patched_check_if_valid_scroll
# -----------------------------------------------------------------------

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FS = 44100
CHANNELS = 2


def natural_sort_key(s):
    """Funkcja sortowania naturalnego (np. plik1, plik2, plik10 zamiast plik1, plik10, plik2)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


class OggRecorderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OGG Tree Audio Recorder")
        self.geometry("900x650")
        self.minsize(800, 550)

        self.src_dir = ""
        self.dst_dir = ""
        self.ogg_files = []
        self.current_index = 0
        self.is_recording = False

        self._build_ui()

    def _build_ui(self):
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.pack(fill="x", padx=15, pady=10)

        self.btn_src = ctk.CTkButton(
            self.top_frame, text="Wybierz folder ŹRÓDŁOWY", command=self.select_src
        )
        self.btn_src.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.lbl_src = ctk.CTkLabel(self.top_frame, text="Brak wybranego folderu", anchor="w")
        self.lbl_src.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        self.btn_dst = ctk.CTkButton(
            self.top_frame, text="Wybierz folder DOCELOWY", command=self.select_dst
        )
        self.btn_dst.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.lbl_dst = ctk.CTkLabel(self.top_frame, text="Brak wybranego folderu", anchor="w")
        self.lbl_dst.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.top_frame.grid_columnconfigure(1, weight=1)

        self.main_panel = ctk.CTkFrame(self)
        self.main_panel.pack(fill="both", expand=True, padx=15, pady=5)

        self.left_frame = ctk.CTkFrame(self.main_panel, width=300)
        self.left_frame.pack(side="left", fill="both", padx=10, pady=10)

        self.lbl_list_title = ctk.CTkLabel(
            self.left_frame, text="Lista plików OGG (0):", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_list_title.pack(anchor="w", padx=10, pady=5)

        self.scroll_files = ctk.CTkScrollableFrame(self.left_frame)
        self.scroll_files.pack(fill="both", expand=True, padx=5, pady=5)

        self.right_frame = ctk.CTkFrame(self.main_panel)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.lbl_progress = ctk.CTkLabel(
            self.right_frame, text="Plik 0 z 0", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_progress.pack(anchor="w", padx=15, pady=(15, 5))

        self.lbl_filename = ctk.CTkLabel(
            self.right_frame, text="Nie załadowano plików", font=ctk.CTkFont(size=16)
        )
        self.lbl_filename.pack(anchor="w", padx=15, pady=5)

        self.txt_src_path = ctk.CTkTextbox(self.right_frame, height=45)
        self.txt_src_path.pack(fill="x", padx=15, pady=5)
        self.txt_src_path.insert("1.0", "Ścieżka źródłowa: -")
        self.txt_src_path.configure(state="disabled")

        self.txt_dst_path = ctk.CTkTextbox(self.right_frame, height=45)
        self.txt_dst_path.pack(fill="x", padx=15, pady=5)
        self.txt_dst_path.insert("1.0", "Ścieżka docelowa: -")
        self.txt_dst_path.configure(state="disabled")

        self.rec_control_frame = ctk.CTkFrame(self.right_frame)
        self.rec_control_frame.pack(fill="x", padx=15, pady=15)

        self.lbl_duration = ctk.CTkLabel(self.rec_control_frame, text="Max czas nagrywania (sekundy):")
        self.lbl_duration.pack(side="left", padx=10, pady=10)

        self.ent_duration = ctk.CTkEntry(self.rec_control_frame, width=60)
        self.ent_duration.pack(side="left", padx=5, pady=10)
        self.ent_duration.insert(0, "3.0")

        self.action_frame = ctk.CTkFrame(self.right_frame)
        self.action_frame.pack(fill="x", padx=15, pady=10)

        self.btn_play_orig = ctk.CTkButton(
            self.action_frame, text="▶ Odtwórz oryginał", command=self.play_original
        )
        self.btn_play_orig.grid(row=0, column=0, padx=5, pady=10)

        self.btn_record = ctk.CTkButton(
            self.action_frame,
            text="🎙 NAGRAJ NOWY DŹWIĘK",
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self.start_recording,
        )
        self.btn_record.grid(row=0, column=1, padx=5, pady=10)

        self.btn_play_my = ctk.CTkButton(
            self.action_frame, text="▶ Odtwórz moje nagranie", command=self.play_recorded
        )
        self.btn_play_my.grid(row=0, column=2, padx=5, pady=10)

        self.nav_frame = ctk.CTkFrame(self.right_frame)
        self.nav_frame.pack(fill="x", padx=15, pady=10)

        self.btn_prev = ctk.CTkButton(self.nav_frame, text="◄ Poprzedni", command=self.prev_file)
        self.btn_prev.pack(side="left", padx=10, pady=10)

        self.btn_next = ctk.CTkButton(self.nav_frame, text="Następny ►", command=self.next_file)
        self.btn_next.pack(side="right", padx=10, pady=10)

        self.lbl_status = ctk.CTkLabel(
            self.right_frame, text="Wybierz foldery, aby rozpocząć.", text_color="gray"
        )
        self.lbl_status.pack(anchor="w", padx=15, pady=10)

    def stop_playback(self):
        """Bezpieczne zatrzymanie odtwarzania w pygame."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def select_src(self):
        folder = filedialog.askdirectory(title="Wybierz folder źródłowy")
        if folder:
            self.src_dir = folder
            self.lbl_src.configure(text=folder)
            self.stop_playback()
            self.scan_and_load_files()

    def select_dst(self):
        folder = filedialog.askdirectory(title="Wybierz folder docelowy")
        if folder:
            self.dst_dir = folder
            self.lbl_dst.configure(text=folder)
            if self.ogg_files:
                self.update_current_file_view()

    def scan_and_load_files(self):
        if not self.src_dir:
            return

        self.ogg_files = []
        for root, dirs, files in os.walk(self.src_dir):
            dirs.sort(key=natural_sort_key)
            for f in sorted(files, key=natural_sort_key):
                if f.lower().endswith(".ogg"):
                    self.ogg_files.append(os.path.join(root, f))

        self.ogg_files.sort(key=natural_sort_key)

        for widget in self.scroll_files.winfo_children():
            widget.destroy()

        self.lbl_list_title.configure(text=f"Lista plików OGG ({len(self.ogg_files)}):")

        if not self.ogg_files:
            messagebox.showinfo("Informacja", "Nie znaleziono plików .ogg w tym folderze.")
            return

        for idx, src_path in enumerate(self.ogg_files):
            rel_path = os.path.relpath(src_path, self.src_dir)
            btn = ctk.CTkButton(
                self.scroll_files,
                text=rel_path,
                anchor="w",
                fg_color="transparent",
                text_color=("black", "white"),
                command=lambda i=idx: self.select_file_by_index(i),
            )
            btn.pack(fill="x", pady=2)

        self.current_index = 0
        self.update_current_file_view()

    def select_file_by_index(self, index):
        self.current_index = index
        self.update_current_file_view()
        self.play_original()

    def update_current_file_view(self):
        if not self.ogg_files:
            return

        src_path = self.ogg_files[self.current_index]
        rel_path = os.path.relpath(src_path, self.src_dir)
        dst_path = os.path.join(self.dst_dir, rel_path) if self.dst_dir else "Nie wybrano folderu docelowego"

        total = len(self.ogg_files)
        self.lbl_progress.configure(text=f"Plik [{self.current_index + 1} / {total}]")
        self.lbl_filename.configure(text=os.path.basename(src_path))

        self.txt_src_path.configure(state="normal")
        self.txt_src_path.delete("1.0", "end")
        self.txt_src_path.insert("1.0", f"Źródło: {src_path}")
        self.txt_src_path.configure(state="disabled")

        self.txt_dst_path.configure(state="normal")
        self.txt_dst_path.delete("1.0", "end")
        self.txt_dst_path.insert("1.0", f"Cel: {dst_path}")
        self.txt_dst_path.configure(state="disabled")

        self.lbl_status.configure(text="Gotowy do nagrywania / odtwarzania.")

    def countdown(self, remaining):
        if not self.is_recording or remaining <= 0:
            return

        self.lbl_status.configure(
            text=f"🎙 NAGRYWANIE... Pozostało max {remaining}s (kliknij Stop, aby zakończyć)",
            text_color="#d9534f"
        )

        self.after(1000, lambda: self.countdown(remaining - 1))

    def _play_file(self, path):
        try:
            self.stop_playback()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.lbl_status.configure(text=f"▶ Odtwarzanie: {os.path.basename(path)}")
        except Exception as e:
            self.lbl_status.configure(text=f"Błąd odtwarzania: {e}")

    def play_original(self):
        if not self.ogg_files:
            return
        src_path = self.ogg_files[self.current_index]
        self._play_file(src_path)

    def play_recorded(self):
        if not self.dst_dir or not self.ogg_files:
            messagebox.showwarning("Ostrzeżenie", "Wybierz najpierw folder docelowy!")
            return

        src_path = self.ogg_files[self.current_index]
        rel_path = os.path.relpath(src_path, self.src_dir)
        dst_path = os.path.join(self.dst_dir, rel_path)

        if not os.path.exists(dst_path):
            messagebox.showinfo("Brak pliku", "Nie nagrano jeszcze pliku dla tego miejsca.")
            return

        self._play_file(dst_path)

    def start_recording(self):
        if not self.dst_dir:
            messagebox.showwarning("Brak folderu", "Wybierz najpierw folder docelowy!")
            return

        if not self.ogg_files:
            messagebox.showwarning("Brak plików", "Wybierz folder źródłowy z plikami .ogg!")
            return

        if self.is_recording:
            return

        try:
            duration = float(self.ent_duration.get())
        except ValueError:
            duration = 3.0
            self.ent_duration.delete(0, "end")
            self.ent_duration.insert(0, "3.0")

        src_path = self.ogg_files[self.current_index]
        rel_path = os.path.relpath(src_path, self.src_dir)
        dst_path = os.path.join(self.dst_dir, rel_path)

        self.stop_playback()

        threading.Thread(
            target=self._record_audio_thread,
            args=(dst_path, duration),
            daemon=True,
        ).start()

        self.countdown(int(duration))

    def stop_recording(self):
        self.is_recording = False

    def _reset_record_button(self):
        self.btn_record.configure(
            text="🎙 NAGRAJ NOWY DŹWIĘK",
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self.start_recording,
            state="normal"
        )

    def _record_audio_thread(self, dst_path, max_duration):
        self.is_recording = True

        self.after(0, lambda: self.btn_record.configure(
            text="⏹ ZATRZYMAJ NAGRYWANIE",
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.stop_recording
        ))

        frames = []

        def callback(indata, frame_count, time_info, status):
            if self.is_recording:
                frames.append(indata.copy())

        try:
            os.path.dirname(dst_path) and os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            with sd.InputStream(samplerate=FS, channels=CHANNELS, dtype="float32", callback=callback):
                start_time = time.time()
                while self.is_recording and (time.time() - start_time < max_duration):
                    sd.sleep(100)

            self.is_recording = False

            if not frames:
                self.after(0, lambda: self.lbl_status.configure(
                    text="Nie nagrano żadnego dźwięku.", text_color="#d9534f"
                ))
                return

            rec_data = np.concatenate(frames, axis=0)

            self.after(0, lambda: self.lbl_status.configure(
                text="Przetwarzanie i zapis OGG...", text_color="orange"
            ))

            sf.write(dst_path, rec_data, FS, format="OGG", subtype="VORBIS")

            self.after(0, lambda: self.lbl_status.configure(
                text=f"✓ Zapisano w: {os.path.basename(dst_path)}",
                text_color="green",
            ))

        except Exception as e:
            self.after(0, lambda: self.lbl_status.configure(
                text=f"Błąd nagrywania: {e}", text_color="#d9534f"
            ))
        finally:
            self.is_recording = False
            self.after(0, self._reset_record_button)

    def prev_file(self):
        if self.ogg_files and self.current_index > 0:
            self.current_index -= 1
            self.update_current_file_view()
            self.play_original()

    def next_file(self):
        if self.ogg_files and self.current_index < len(self.ogg_files) - 1:
            self.current_index += 1
            self.update_current_file_view()
            self.play_original()


if __name__ == "__main__":
    app = OggRecorderApp()
    app.mainloop()
