# reazon-stt

[ReazonSpeech-k2-v2](https://research.reazon.jp/projects/ReazonSpeech/) を使った Windows 向け音声入力ツール。
ホットキーで録音し、認識結果をカーソル位置に貼り付ける。

Qwen3-ASR（CPU: 30秒/発話）の代替。ReazonSpeechは同等精度で0.3秒/発話。

## 前提条件

- Windows 10/11 (x64)
- Python 3.10+
- CPU のみで動作（GPU不要）

## セットアップ

```bash
pip install sherpa-onnx sounddevice pynput numpy
```

モデルファイル（int8、約153MB）は初回起動時に自動ダウンロードされる。

## 使い方

```bash
python stt.py
```

- `Ctrl+Shift+R` : 録音開始 → 2秒無音で自動停止 → カーソル位置にテキスト貼り付け
- 録音中に再度 `Ctrl+Shift+R` で手動停止も可
- `Ctrl+C` : 終了

## ファイル構成

- `stt.py` - エントリポイント、ホットキー制御
- `recognizer.py` - モデル読込、音声認識、テキスト正規化
- `recorder.py` - 録音制御、無音検出
- `clipboard.py` - Win32 クリップボード操作
- `model/` - ReazonSpeech-k2-v2 モデルファイル（自動ダウンロード、gitignore）

## モデル

[csukuangfj/reazonspeech-k2-v2](https://huggingface.co/csukuangfj/reazonspeech-k2-v2) の int8 量子化版を使用。

- パラメータ: 159M
- モデルサイズ: 153MB (int8)
- CER: 6.5% (JSUT) / 7.9% (CommonVoice 8)
- 推論速度: 約0.3秒/5秒発話 (CPU)
