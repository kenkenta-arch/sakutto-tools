#!/usr/bin/env python3
"""短いカットをつないだ縦長ショート（1080x1920・画面いっぱい）を作る。

使い方:
  python3 montage.py spec.json --out 書き出し/clip_v2_en.mp4

spec.json の例:
{
  "source": "素材/heismay_trailer.mp4",
  "font": "Hiragino Sans",
  "cuts": [
    {"start": 45.0, "end": 46.0, "zoom": 1.0},
    {"start": 43.0, "end": 44.8, "zoom": 1.1}
  ],
  "captions": [
    {"start": 0.0, "end": 1.0, "text": "THIS LITTLE GUY"}
  ]
}

・各カットは、元の横長映像の中央を縦長に切り抜いて画面いっぱいに表示する（zoom で少し寄れる、x_offset で左右にずらせる）
・"mode": "fit" のカットは、横長の全体を見せ、背景は同じ映像を大きくぼかす（左右に大事なものがある場面用）
・テロップは画面の中央付近に、大きな白文字・黒い縁取りで、数語ずつ出す（出る瞬間に少し大きく見せる）
・音声は各カットの元の音をそのままつなぐ
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def ass_time(x):
    h, r = divmod(max(0, x), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(spec):
    font = spec.get("font", "Hiragino Sans")
    size = spec.get("caption_size", 110)
    y = spec.get("caption_y", 760)  # 下からの位置
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,9,4,2,60,60,{y},1
Style: Accent,{font},{size},&H0000E5FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,9,4,2,60,60,{y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for c in spec.get("captions", []):
        style = "Accent" if c.get("accent") else "Cap"
        text = c["text"].replace("\n", r"\N")
        pop = r"{\fscx118\fscy118\t(0,120,\fscx100\fscy100)}"  # 出る瞬間に少し大きく
        ev.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},{style},,0,0,0,,{pop}{text}")
    return head + "\n".join(ev) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    src = spec["source"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, c in enumerate(spec["cuts"]):
            z = float(c.get("zoom", 1.0))
            h = int(1920 * z) // 2 * 2
            if c.get("mode") == "fit":  # 横長の全体を見せたい場面：全体を表示し、背景は同じ映像を大きくぼかす
                vf = ("split=2[bg][fg];[bg]scale=-2:1920,crop=1080:1920,gblur=sigma=25[b];"
                      f"[fg]scale={int(1080 * z)}:-2,crop=1080:ih[f];[b][f]overlay=(W-w)/2:(H-h)/2,"
                      "setsar=1,fps=30,format=yuv420p")
            else:
                vf = (f"scale=-2:{h},crop=1080:1920:(iw-1080)/2+{int(c.get('x_offset', 0))}:(ih-1920)/2,"
                      "setsar=1,fps=30,format=yuv420p")
            p = Path(td) / f"p{i:02d}.mp4"
            cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-ss", f"{c['start']:.3f}", "-to", f"{c['end']:.3f}", "-i", src,
                   "-vf", vf, "-af", "aresample=48000",
                   "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", str(p)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                sys.exit(1)
            parts.append(p)
        lst = Path(td) / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        joined = Path(td) / "joined.mp4"
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                            "-i", str(lst), "-c", "copy", str(joined)], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            sys.exit(1)
        ass = Path(td) / "cap.ass"
        ass.write_text(build_ass(spec), encoding="utf-8")
        esc = str(ass).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(joined),
                            "-vf", f"subtitles='{esc}'", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                            "-c:a", "copy", "-movflags", "+faststart", str(out)], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr, file=sys.stderr)
            sys.exit(1)
    print(f"書き出し完了: {out}")


if __name__ == "__main__":
    main()
