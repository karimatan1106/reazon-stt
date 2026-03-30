"""録音制御 - 無音検出による自動停止付きマイク録音"""

import time
import wave
import threading
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.005
SILENCE_DURATION = 2.0
MIN_RECORD_DURATION = 1.0
BEEP_RATE = 44100


def beep(freq=800, duration=0.15):
    t = np.linspace(0, duration, int(BEEP_RATE * duration), False)
    tone = 0.3 * np.sin(2 * np.pi * freq * t).astype(np.float32)
    sd.play(tone, samplerate=BEEP_RATE)
    sd.wait()


def save_wav(audio_chunks, wav_path):
    audio = np.concatenate(audio_chunks, axis=0).flatten()
    audio_int16 = (audio * 32767).astype(np.int16)
    with wave.open(wav_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


class Recorder:
    def __init__(self, on_audio_ready):
        self._on_audio_ready = on_audio_ready
        self._recording = False
        self._stream = None
        self._chunks = []
        self._mode = "paste"

    @property
    def recording(self):
        return self._recording

    def toggle(self, mode="paste"):
        if not self._recording:
            self._mode = mode
            self._start()
        else:
            self._stop_and_process()

    def _start(self):
        self._recording = True
        self._chunks.clear()
        silence_start = [None]
        record_start = [time.perf_counter()]

        def callback(indata, frames, time_info, status):
            if not self._recording:
                return
            self._chunks.append(indata.copy())
            elapsed = time.perf_counter() - record_start[0]
            if elapsed < MIN_RECORD_DURATION:
                return
            rms = np.sqrt(np.mean(indata ** 2))
            if rms < SILENCE_THRESHOLD:
                if silence_start[0] is None:
                    silence_start[0] = time.perf_counter()
                elif time.perf_counter() - silence_start[0] > SILENCE_DURATION:
                    self._recording = False
                    threading.Thread(
                        target=self._stop_and_process, daemon=True
                    ).start()
            else:
                silence_start[0] = None

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1,
            dtype="float32", callback=callback, blocksize=1024,
        )
        self._stream.start()
        beep(800, 0.15)
        label = "CLAUDE" if self._mode == "claude" else "PASTE"
        print(f"Recording [{label}]... (auto-stop on silence)", flush=True)

    def _stop_and_process(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._recording = False
        beep(400, 0.15)
        print("Recognizing...", flush=True)
        self._on_audio_ready(list(self._chunks), self._mode)
