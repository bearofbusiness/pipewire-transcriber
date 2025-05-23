# PipeWire Transcriber

A lightweight GUI application for capturing PipeWire (PulseAudio) monitor audio and transcribing it in near real-time using OpenAI’s Whisper model via the `faster-whisper` library.

---

## Features

* **Desktop Audio Capture**: Records audio from your system’s `.monitor` source (e.g., speakers) using `parec` (PulseAudio recorder).
* **Live Transcription**: Streams chunks of audio into Whisper for continuous transcription.
* **Model Selection**: Choose between `tiny`, `base`, `small`, `medium`, or `large` Whisper models.
* **Compute Device & Precision**: Select CPU or CUDA (GPU) and quantization (`float16` or `int8_float16`) for performance/accuracy trade-offs.
* **GTK4 GUI**: Simple interface built with PyGObject and GTK4.

---

## Prerequisites

1. **Python 3.13+**
2. **PulseAudio utilities** (for `parec`):

   ```bash
   sudo apt install pulseaudio-utils    # Debian/Ubuntu
   sudo pacman -S pulseaudio            # Arch
   ```
3. **PipeWire with PulseAudio compatibility**
4. **Required Python packages** (install in a virtual environment):

   ```bash
   pip install sounddevice numpy faster-whisper pygobject pulsectl
   ```
5. **Optional (GPU)**: CUDA drivers + PyTorch/CUDA support for Whisper on GPU.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/bearofbusiness/pipewire-transcriber.git
cd pipewire-transcriber

# Create and activate a virtual env
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** If you plan to use GPU acceleration, ensure you have CUDA properly installed and that `faster-whisper` picks up your GPU driver.

---

## Usage

1. Launch the app:

   ```bash
   python main.py
   ```
2. In the GUI:

   * **Monitor Source**: Select the `.monitor` sink for your desktop audio.
   * **Model Size**: Pick one of `tiny`, `base`, `small`, `medium`, or `large`. Larger models yield better accuracy but use more RAM/CPU/GPU.
   * **Compute Device**: Choose `cpu` or `cuda` (if available).
   * **Compute Type**: Select `default` (float32), `float16`, or `int8_float16` (quantized).
3. Click **Start** to begin capturing and transcribing.
4. Transcriptions appear in the main text area in (near) real-time.
5. Click **Stop** to end the session.
6. Click **Clear** to clear the text.

---

## Troubleshooting

* \`\`\*\* errors\*\*: Ensure PulseAudio is running and your monitor source is listed in `pactl list sources short`.
* **No audio captured**: Confirm PipeWire’s Pulse compatibility is active (e.g., `pipewire-pulse` service).
* **Whisper model download issues**: You may need `huggingface_hub[hf_xet]` for faster downloads:

  ```bash
  pip install huggingface_hub[hf_xet]
  ```

---

## Contributing

PRs welcome!

---

## License

MIT © \bearofbusiness

---

Happy transcribing!
