"""ReazonSpeech-k2-v2 音声認識エンジン"""

import os
import re
import shutil
import tempfile
import time
import urllib.request
import wave
import numpy as np

SAMPLE_RATE = 16000
_HF_BASE = "https://huggingface.co/csukuangfj/reazonspeech-k2-v2/resolve/main"
MODEL_FILES = [
    "encoder-epoch-99-avg-1.int8.onnx",
    "decoder-epoch-99-avg-1.int8.onnx",
    "joiner-epoch-99-avg-1.int8.onnx",
    "tokens.txt",
]

_FULLWIDTH = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ" \
             "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ" \
             "０１２３４５６７８９"
_HALFWIDTH = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
             "abcdefghijklmnopqrstuvwxyz" \
             "0123456789"
_NORMALIZE_TABLE = str.maketrans(_FULLWIDTH, _HALFWIDTH)


def _download_models(model_dir):
    """HuggingFaceからモデルを自動ダウンロード"""
    os.makedirs(model_dir, exist_ok=True)
    for f in MODEL_FILES:
        path = os.path.join(model_dir, f)
        if os.path.exists(path):
            continue
        url = f"{_HF_BASE}/{f}"
        print(f"Downloading {f}...", flush=True)
        urllib.request.urlretrieve(url, path)
    print("Model download complete.", flush=True)


def _resolve_model_dir():
    """モデルディレクトリを解決。未DLなら自動DL、非ASCIIパスならtempにコピー"""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
    _download_models(src)
    if src.isascii():
        return src
    dst = os.path.join(tempfile.gettempdir(), "sherpa_onnx_model")
    os.makedirs(dst, exist_ok=True)
    for f in MODEL_FILES:
        s, d = os.path.join(src, f), os.path.join(dst, f)
        if not os.path.exists(d) or os.path.getsize(s) != os.path.getsize(d):
            shutil.copy2(s, d)
    return dst


def load_model():
    import sherpa_onnx

    model_dir = _resolve_model_dir()
    print("ReazonSpeech-k2-v2 loading...", flush=True)
    t0 = time.perf_counter()
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(model_dir, MODEL_FILES[0]),
        decoder=os.path.join(model_dir, MODEL_FILES[1]),
        joiner=os.path.join(model_dir, MODEL_FILES[2]),
        tokens=os.path.join(model_dir, MODEL_FILES[3]),
        num_threads=4,
        sample_rate=SAMPLE_RATE,
        feature_dim=80,
        decoding_method="greedy_search",
    )
    print(f"Model loaded in {time.perf_counter() - t0:.1f}s", flush=True)
    return rec


def normalize_text(text):
    text = text.translate(_NORMALIZE_TABLE)
    text = re.sub(r'(?<=[A-Za-z0-9]) (?=[A-Za-z0-9])', '', text)
    return text.strip()


def transcribe(recognizer, wav_path):
    with wave.open(wav_path, "r") as wf:
        data = wf.readframes(wf.getnframes())
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, samples.tolist())
    recognizer.decode_stream(stream)
    return normalize_text(stream.result.text)
