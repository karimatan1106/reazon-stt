"""ReazonSpeech-k2-v2 音声入力ツール - ホットキーで録音→カーソル位置に貼り付け"""

import sys
import os
import time
import tempfile
import threading

from clipboard import paste_text
from claude_runner import send_to_claude
from recognizer import load_model, transcribe
from recorder import Recorder, save_wav, SILENCE_DURATION

WAV_PATH = os.path.join(tempfile.gettempdir(), "stt_tmp.wav")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from pynput import keyboard as pynput_kb

    recognizer = load_model()

    print(f"\n{'='*50}")
    print(f"  ReazonSpeech STT")
    print(f"  Ctrl+Shift+R: 音声→テキスト貼り付け")
    print(f"  Ctrl+Shift+E: 音声→Claude Code実行")
    print(f"  {SILENCE_DURATION}秒無音で自動停止")
    print(f"  Ctrl+C で終了")
    print(f"{'='*50}\n")
    print("Ready.\n", flush=True)

    def on_audio_ready(chunks, mode="paste"):
        if not chunks:
            print("No audio captured\n")
            return
        save_wav(chunks, WAV_PATH)
        t0 = time.perf_counter()
        text = transcribe(recognizer, WAV_PATH)
        elapsed = time.perf_counter() - t0
        if not text:
            print(f"  [{elapsed:.1f}s] (no speech detected)\n", flush=True)
            return
        print(f"  [{elapsed:.1f}s] {text}", flush=True)
        if mode == "claude":
            result = send_to_claude(text)
            if result:
                print(f"\n{result}\n", flush=True)
        else:
            paste_text(text)
            print(flush=True)

    recorder = Recorder(on_audio_ready)
    pressed_keys = set()

    def on_press(key):
        pressed_keys.add(key)
        ctrl = any(k in pressed_keys for k in (
            pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r, pynput_kb.Key.ctrl))
        shift = any(k in pressed_keys for k in (
            pynput_kb.Key.shift_l, pynput_kb.Key.shift_r, pynput_kb.Key.shift))
        vk = getattr(key, 'vk', None)
        if ctrl and shift and vk == 82:
            threading.Thread(
                target=lambda: recorder.toggle("paste"), daemon=True
            ).start()
        elif ctrl and shift and vk == 69:
            threading.Thread(
                target=lambda: recorder.toggle("claude"), daemon=True
            ).start()

    def on_release(key):
        pressed_keys.discard(key)

    listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    try:
        while listener.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop()
        print("\nStopped.")


if __name__ == "__main__":
    main()
