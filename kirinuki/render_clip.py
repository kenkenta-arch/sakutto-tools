#!/usr/bin/env python3
"""縦長（1080x1920）の切り抜き動画を書き出す。

使い方:
  python3 render_clip.py 素材/trailer.mp4 --start 12.5 --end 42.5 \
      --hook "このキャラ、強すぎない？" --subs 候補/transcript.srt \
      --out 書き出し/clip01_ja.mp4

レイアウト:
  ・背景：同じ映像をぼかして画面いっぱいに
  ・中央：元の横長映像を幅いっぱいに
  ・上：冒頭テロップ（ひとこと）。白文字・黒い縁取り
  ・下：字幕（--subs を渡したとき。元動画の時間のSRTを、切り出し位置に合わせてずらす）

スタイル（字幕の大きさ・色・位置）は --style に JSON を渡すと上書きできる。
見本を分析した結果（参考/スタイル.md）に合わせて調整する。
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_STYLE = {
    "font": "Hiragino Sans",          # Mac。無ければ fontconfig が近いものを選ぶ
    "hook_size": 78,
    "hook_y": 330,                    # 上からの位置(px)
    "hook_color": "&H00FFFFFF",       # ASS形式 &HAABBGGRR
    "hook_outline": 6,
    "sub_size": 64,
    "sub_margin_v": 420,              # 下からの位置(px)
    "sub_color": "&H0000F0FF",        # 黄色
    "sub_outline": 5,
    "max_chars": 16,                  # 1行の最大文字数（日本語）。英語は単語で折り返す
}


def parse_srt(text):
    blocks = re.split(r"\n\s*\n", text.strip())
    out = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) < 2:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1] if "-->" in lines[1] else lines[0])
        if not m:
            continue
        g = list(map(int, m.groups()))
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        body = lines[2:] if "-->" in lines[1] else lines[1:]
        out.append((s, e, "\n".join(body).strip()))
    return out


def ass_time(x):
    x = max(0, x)
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, max_chars):
    if "\n" in text:  # 改行の位置を指定したときは、そのとおりに改行する
        return r"\N".join(t.strip() for t in text.split("\n"))
    if re.search(r"[぀-ヿ一-鿿]", text):
        return r"\N".join(text[i:i + max_chars] for i in range(0, len(text), max_chars))
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > max_chars * 2:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return r"\N".join(lines)


def build_ass(style, hook, subs, start, end):
    st = style
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{st['font']},{st['hook_size']},{st['hook_color']},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{st['hook_outline']},2,8,60,60,{st['hook_y']},1
Style: Sub,{st['font']},{st['sub_size']},{st['sub_color']},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{st['sub_outline']},2,2,60,60,{st['sub_margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    dur = end - start
    if hook:
        ev.append(f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Hook,,0,0,0,,{wrap(hook, st['max_chars'])}")
    for s, e, t in subs:
        if e <= start or s >= end:
            continue
        ev.append(f"Dialogue: 0,{ass_time(s - start)},{ass_time(min(e, end) - start)},Sub,,0,0,0,,{wrap(t, st['max_chars'])}")
    return head + "\n".join(ev) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--hook", default="", help="冒頭テロップ（ひとこと）")
    ap.add_argument("--subs", default=None, help="元動画の時間のSRT（任意）")
    ap.add_argument("--style", default=None, help="スタイルを上書きするJSON（文字列かファイル）")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    style = dict(DEFAULT_STYLE)
    if a.style:
        p = Path(a.style)
        style.update(json.loads(p.read_text(encoding="utf-8") if p.exists() else a.style))

    subs = parse_srt(Path(a.subs).read_text(encoding="utf-8")) if a.subs else []
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        ass = Path(td) / "overlay.ass"
        ass.write_text(build_ass(style, a.hook, subs, a.start, a.end), encoding="utf-8")
        esc = str(ass).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        vf = (
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.08[bgb];"
            "[fg]scale=1080:-2[fgs];"
            "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p,"
            f"subtitles='{esc}'[v]"
        )
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-ss", f"{a.start:.3f}", "-to", f"{a.end:.3f}", "-i", a.video,
               "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", "30",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            sys.exit(1)
    print(f"書き出し完了: {out}")


if __name__ == "__main__":
    main()
