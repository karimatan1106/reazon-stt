"""Windows クリップボード経由のテキスト貼り付け"""

import time
import ctypes


def paste_text(text):
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    VK_CONTROL = 0x11
    VK_V = 0x56
    KEYEVENTF_KEYUP = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # x64ポインタ型を正しく設定
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

    # クリップボード履歴除外フラグを登録
    exclude_fmt = user32.RegisterClipboardFormatW(
        "ExcludeClipboardContentFromMonitorProcessing")

    # 元のクリップボード内容を退避
    old_clip = None
    if user32.OpenClipboard(0):
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if h:
            p = kernel32.GlobalLock(h)
            if p:
                old_clip = ctypes.wstring_at(p)
                kernel32.GlobalUnlock(h)
        user32.CloseClipboard()

    # 履歴に残さずクリップボードにセット
    encoded = text.encode("utf-16-le") + b"\x00\x00"
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    p = kernel32.GlobalLock(h_mem)
    ctypes.memmove(p, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)

    if user32.OpenClipboard(0):
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
        # 履歴除外マーカーをセット
        if exclude_fmt:
            h_ex = kernel32.GlobalAlloc(GMEM_MOVEABLE, 1)
            p_ex = kernel32.GlobalLock(h_ex)
            ctypes.memset(p_ex, 0, 1)
            kernel32.GlobalUnlock(h_ex)
            user32.SetClipboardData(exclude_fmt, h_ex)
        user32.CloseClipboard()

    time.sleep(0.1)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # 元のクリップボードを復元（Ctrl+V完了を待ってから）
    time.sleep(0.5)
    if old_clip is not None:
        encoded = old_clip.encode("utf-16-le") + b"\x00\x00"
        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
        p = kernel32.GlobalLock(h_mem)
        ctypes.memmove(p, encoded, len(encoded))
        kernel32.GlobalUnlock(h_mem)
        for _ in range(5):
            if user32.OpenClipboard(0):
                user32.EmptyClipboard()
                user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                user32.CloseClipboard()
                break
            time.sleep(0.1)
    else:
        # 元が空だった場合もクリアして音声テキストを残さない
        for _ in range(5):
            if user32.OpenClipboard(0):
                user32.EmptyClipboard()
                user32.CloseClipboard()
                break
            time.sleep(0.1)
