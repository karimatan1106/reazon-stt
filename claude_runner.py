"""Claude Code CLI 連携"""

import os
import shutil
import time
import subprocess
import json

_session_id = None


def _find_claude_cli():
    """PATHおよび既知のインストール先からclaude CLIを探す"""
    found = shutil.which("claude")
    if found:
        return found
    candidates = [
        os.path.expanduser("~/.local/bin/claude.exe"),
        os.path.expanduser("~/AppData/Roaming/npm/claude.cmd"),
        os.path.expanduser("~/AppData/Roaming/npm/claude"),
        "C:/Program Files/nodejs/claude.cmd",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def send_to_claude(text):
    global _session_id

    claude_cli = _find_claude_cli()
    if not claude_cli:
        _print_setup_guide()
        return None

    print(f"  Claude処理中...", flush=True)
    msg = json.dumps({
        "type": "user",
        "message": {"role": "user", "content": text},
    })
    cmd = [claude_cli, "-p", "--input-format", "stream-json",
           "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions",
           "--mcp-config", '{"mcpServers":{}}', "--strict-mcp-config",
           "--append-system-prompt",
           "絶対ルール: **太字**や__下線__は禁止。"
           "アスタリスク2つで囲む記法を一切使うな。"
           "見出し(#)・箇条書き(-)・コードブロック(```)のみ許可。"]
    if _session_id:
        cmd += ["--resume", _session_id]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        proc.stdin.write((msg + "\n").encode("utf-8"))
        proc.stdin.close()
        t0 = time.perf_counter()
        result_text = ""
        for line in proc.stdout:
            data = line.decode("utf-8", errors="replace").strip()
            if not data:
                continue
            elapsed = int(time.perf_counter() - t0)
            print(f"\r  Claude応答待ち... {elapsed}s", end="", flush=True)
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "result":
                    result_text = parsed.get("result", "")
                    sid = parsed.get("session_id")
                    if sid:
                        _session_id = sid
                    break
            except Exception:
                pass
        print(flush=True)
        proc.wait(timeout=5)
        return result_text if result_text else None
    except FileNotFoundError:
        _print_setup_guide()
        return None
    except Exception as e:
        print(f"  Claude error: {e}", flush=True)
        return None


def _print_setup_guide():
    print("\n  Claude CLI が見つかりません。", flush=True)
    print("  以下の手順でセットアップしてください:\n", flush=True)
    print("  [1] Node.js インストール (未導入の場合)", flush=True)
    print("      https://nodejs.org/ からLTS版をダウンロード", flush=True)
    print("      インストール後、ターミナルを再起動\n", flush=True)
    print("  [2] Claude Code インストール", flush=True)
    print("      npm install -g @anthropic-ai/claude-code\n", flush=True)
    print("  [3] 認証 (どちらか一方)\n", flush=True)
    print("      A) Claudeアカウントでログイン:", flush=True)
    print("         ターミナルで claude login を実行", flush=True)
    print("         ブラウザが開くのでClaudeアカウントで認証", flush=True)
    print("         Max/Proプランが必要\n", flush=True)
    print("      B) APIキーを環境変数にセット:", flush=True)
    print("         https://console.anthropic.com/settings/keys でキー発行", flush=True)
    print("         ターミナルで以下を実行:", flush=True)
    print("           set ANTHROPIC_API_KEY=sk-ant-...  (現在のセッションのみ)", flush=True)
    print("           setx ANTHROPIC_API_KEY sk-ant-... (永続化、次回起動から有効)", flush=True)
    print("         または Windows設定 → システム → バージョン情報 →", flush=True)
    print("           システムの詳細設定 → 環境変数 で追加\n", flush=True)
