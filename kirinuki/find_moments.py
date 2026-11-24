#!/usr/bin/env python3
"""盛り上がる場面の候補を探す。

使い方:
  python3 find_moments.py 素材/trailer.mp4 --len 30 --count 8 --out 候補

やること:
  1. 音の大きさ（0.5秒ごと）と、画面の切り替わり（シーンチェンジ）を測る
  2. 「音が大きい」「カットが多い」区間に点数をつけ、重ならないように上位を選ぶ
  3. 候補ごとにサムネイル画像を書き出し、候補一覧（candidates.json / candidates.md）を作る
  4. faster-whisper が入っていれば、文字起こし（transcript.srt）も作り、候補ごとのセリフを載せる

必要なもの: ffmpeg（必須）、faster-whisper（任意）
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)])
    return float(r.stdout.strip())


def loudness_series(path):
    """0.1秒ごとの瞬間ラウドネス(LUFS)を返す。[(time, lufs)]"""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=metadata=0", "-f", "null", "-"])
    out = []
    for m in re.finditer(r"t:\s*([\d.]+)\s+TARGET:.*?M:\s*(-?[\d.]+|-inf)", r.stderr):
        t = float(m.group(1))
        v = m.group(2)
        out.append((t, -70.0 if v == "-inf" else float(v)))
    return out


def scene_times(path, threshold=0.3):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an",
             "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", r.stderr)]


def pick_windows(total, loud, scenes, length, count, step=1.0):
    def loud_avg(a, b):
        vals = [v for t, v in loud if a <= t < b]
        return sum(vals) / len(vals) if vals else -70.0

    def loud_peak(a, b):
        vals = [v for t, v in loud if a <= t < b]
        return max(vals) if vals else -70.0

    cands = []
    t = 0.0
    while t + length <= total + 0.01:
        a, b = t, min(t + length, total)
        cuts = sum(1 for s in scenes if a <= s < b)
        score = (loud_avg(a, b) + 70) * 1.0 + (loud_peak(a, b) + 70) * 0.5 + cuts * 1.5
        cands.append({"start": round(a, 2), "end": round(b, 2), "score": round(score, 2), "cuts": cuts,
                      "loud_avg": round(loud_avg(a, b), 1), "loud_peak": round(loud_peak(a, b), 1)})
        t += step
    cands.sort(key=lambda c: c["score"], reverse=True)
    chosen = []
    for c in cands:
        if all(c["end"] <= x["start"] or c["start"] >= x["end"] for x in chosen):
            chosen.append(c)
        if len(chosen) >= count:
            break
    if not chosen and total > 0:
        chosen = [{"start": 0.0, "end": round(min(length, total), 2), "score": 0, "cuts": 0, "loud_avg": 0, "loud_peak": 0}]
    chosen.sort(key=lambda c: c["start"])
    return chosen


def transcribe(path, outdir, language=None):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(path), language=language, vad_filter=True)
    segs = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]

    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"

    with open(outdir / "transcript.srt", "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n")
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--len", type=float, default=30, help="1本の長さ（秒）")
    ap.add_argument("--count", type=int, default=8, help="候補の数")
    ap.add_argument("--out", default="候補")
    ap.add_argument("--lang", default=None, help="文字起こしの言語（en / ja など。省略で自動判定）")
    a = ap.parse_args()

    src = Path(a.video)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    total = duration(src)
    length = min(a.len, total)
    print(f"動画の長さ: {total:.1f}秒 / 1本 {length:.0f}秒で {a.count}個 探します", file=sys.stderr)

    loud = loudness_series(src)
    scenes = scene_times(src)
    wins = pick_windows(total, loud, scenes, length, a.count)
    segs = transcribe(src, out, a.lang)

    for i, w in enumerate(wins, 1):
        mid = (w["start"] + w["end"]) / 2
        thumb = out / f"候補{i:02d}.jpg"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{mid:.2f}", "-i", str(src),
             "-frames:v", "1", "-vf", "scale=640:-2", str(thumb)])
        w["id"] = i
        w["thumb"] = thumb.name
        if segs:
            w["lines"] = [s["text"] for s in segs if s["end"] > w["start"] and s["start"] < w["end"]]

    (out / "candidates.json").write_text(json.dumps({"source": str(src), "duration": total, "candidates": wins},
                                                     ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# 候補一覧：{src.name}", "", "| 番号 | 時間 | 点数 | カット数 | セリフ |", "|---|---|---|---|---|"]
    for w in wins:
        rng = f"{int(w['start'] // 60)}:{w['start'] % 60:04.1f}〜{int(w['end'] // 60)}:{w['end'] % 60:04.1f}"
        lines = " / ".join(w.get("lines", []))[:80] if segs else "（文字起こしなし）"
        md.append(f"| {w['id']} | {rng} | {w['score']} | {w['cuts']} | {lines} |")
    (out / "candidates.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
