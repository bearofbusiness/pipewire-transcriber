import threading
import subprocess
import sys
import numpy as np
from faster_whisper import WhisperModel
import gi
# Ensure GTK4 is used
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

# Requires pulsectl for listing sources and parec for capture
import pulsectl

# Configuration
PIPEWIRE_RATE = 48000       # Rate from PipeWire monitor
TARGET_RATE = 16000         # Whisper expects 16kHz
CHUNK_DURATION = 3          # seconds per chunk

MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]
DEVICE_CHOICES = ["cpu", "cuda"]
COMPUTE_TYPES = ["default", "float16", "int8_float16"]

class TranscriberApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="PipeWire Transcriber")
        self.set_default_size(700, 550)

        # UI setup
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        self.set_child(vbox)

        # Monitor source selection
        pulse = pulsectl.Pulse('pipewire-transcriber')
        self.monitors = [s for s in pulse.source_list() if s.name.endswith('.monitor')]
        device_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        device_box.append(Gtk.Label(label="Monitor Source:"))
        self.source_combo = Gtk.ComboBoxText()
        for m in self.monitors:
            self.source_combo.append_text(f"{m.name} ({m.description})")
        self.source_combo.set_active(0 if self.monitors else -1)
        self.source_combo.set_sensitive(bool(self.monitors))
        device_box.append(self.source_combo)
        vbox.append(device_box)

        # Model parameters
        param_grid = Gtk.Grid(column_spacing=6, row_spacing=6)
        # Model size
        param_grid.attach(Gtk.Label(label="Model Size:"), 0, 0, 1, 1)
        self.model_combo = Gtk.ComboBoxText()
        for size in MODEL_SIZES:
            self.model_combo.append_text(size)
        self.model_combo.set_active(MODEL_SIZES.index("small"))
        param_grid.attach(self.model_combo, 1, 0, 1, 1)
        # Compute device
        param_grid.attach(Gtk.Label(label="Compute Device:"), 0, 1, 1, 1)
        self.compute_combo = Gtk.ComboBoxText()
        for dev in DEVICE_CHOICES:
            self.compute_combo.append_text(dev)
        self.compute_combo.set_active(0)
        param_grid.attach(self.compute_combo, 1, 1, 1, 1)
        # Compute type
        param_grid.attach(Gtk.Label(label="Compute Type:"), 0, 2, 1, 1)
        self.compute_type_combo = Gtk.ComboBoxText()
        for ct in COMPUTE_TYPES:
            self.compute_type_combo.append_text(ct)
        self.compute_type_combo.set_active(0)
        param_grid.attach(self.compute_type_combo, 1, 2, 1, 1)
        vbox.append(param_grid)

        # Transcript view
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_child(self.textview)
        vbox.append(scrolled)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_start)
        self.stop_btn = Gtk.Button(label="Stop")
        self.stop_btn.connect("clicked", self.on_stop)
        self.stop_btn.set_sensitive(False)
        self.clear_btn = Gtk.Button(label="Clear")
        self.clear_btn.connect("clicked", self.clear_text)
        btn_box.append(self.start_btn)
        btn_box.append(self.stop_btn)
        btn_box.append(self.clear_btn)
        vbox.append(btn_box)

        # State
        self.proc = None
        self.running = False
        self.model = None

        self.append_text("Ready. Pick model/device options and press Start.\n")

    def append_text(self, txt: str):
        GLib.idle_add(self._append, txt)

    def _append(self, txt: str):
        end = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end, txt)

    def on_start(self, btn):
        if self.running:
            return
        # Load model
        size = self.model_combo.get_active_text()
        device = self.compute_combo.get_active_text()
        ct = self.compute_type_combo.get_active_text()
        compute_type = None if ct == "default" else ct
        self.append_text(f"Loading model '{size}' on {device} [{compute_type or 'float32'}]...\n")
        try:
            if compute_type:
                self.model = WhisperModel(size, device=device, compute_type=compute_type)
            else:
                self.model = WhisperModel(size, device=device)
        except Exception as e:
            self.append_text(f"[Error] Failed to load model: {e}\n")
            return
        self.append_text("Model loaded.\n")

        # Start capture
        idx = self.source_combo.get_active()
        src = self.monitors[idx].name if idx >= 0 else None
        cmd = ["parec"] + (['-d', src] if src else []) + ['--format=s16le', f'--rate={PIPEWIRE_RATE}', '--channels=2']
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except Exception as e:
            self.append_text(f"[Error] Failed to start parec: {e}\n")
            return
        self.running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        threading.Thread(target=self.capture_loop, daemon=True).start()
        self.append_text("Transcription started...\n")

    def on_stop(self, btn):
        if not self.running:
            return
        self.running = False
        if self.proc:
            self.proc.terminate()
            self.proc = None
        self.stop_btn.set_sensitive(False)
        self.start_btn.set_sensitive(True)
        self.append_text("Transcription stopped.\n")

    def clear_text(self, btn):
        self.textview.get_buffer().set_text("")
        pass

    def capture_loop(self):
        chunk = int(PIPEWIRE_RATE * CHUNK_DURATION * 2 * 2)
        while self.running:
            raw = self.proc.stdout.read(chunk)
            if not raw:
                break
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            audio = audio.reshape(-1, 2).mean(axis=1)
            if PIPEWIRE_RATE != TARGET_RATE:
                new_len = int(len(audio) * TARGET_RATE / PIPEWIRE_RATE)
                audio = np.interp(np.linspace(0, len(audio), new_len), np.arange(len(audio)), audio)
            segments, _ = self.model.transcribe(audio, beam_size=5)
            text = ''.join(seg.text for seg in segments)
            self.append_text(text + "\n")



if __name__ == "__main__":
    app = TranscriberApp()
    loop = GLib.MainLoop()
    app.connect("close-request", lambda win: (loop.quit(), False))
    app.show()
    loop.run()
