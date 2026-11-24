# 切り抜きの道具（GAME MOMENTS 用）

Claude が使う道具です。オーナーが自分で操作する必要はありません。

## 流れ
1. 素材（公式トレーラーなど、キャンペーンが許可した動画）を `素材/` に入れる
2. `find_moments.py` で盛り上がる場面の候補を出す（サムネイル付きの一覧ができる）
3. オーナーが候補を選ぶ
4. `render_clip.py` で縦長（1080x1920）の動画を書き出す（冒頭テロップ＋字幕）
5. オーナーが確認して、各SNSに投稿 → キャンペーンに提出

## 例
```
python3 find_moments.py 素材/trailer.mp4 --len 30 --count 8 --out 候補 --lang en
python3 render_clip.py 素材/trailer.mp4 --start 12.5 --end 42.5 \
  --hook "Heismay is way too fast" --subs 候補/transcript.srt --out 書き出し/clip01_en.mp4
```

## Mac での準備（最初の1回だけ。Claude が確認しながら入れる）
- Homebrew（Mac 用の道具の入れ物）
- ffmpeg：`brew install ffmpeg`（動画を切ったりつないだりする無料の道具）
- faster-whisper：`pip3 install faster-whisper`（文字起こしをする無料の道具。初回にモデルをダウンロードする）

## 注意
- 素材は、キャンペーンが用意したもの・許可されたものだけを使う
- 字幕は文字起こしの結果をそのまま使わず、聞き間違いを直してから書き出す
- 説明文にはキャンペーンが指定した広告タグ（#Ad など）を必ず入れる
- 2026-11-24：テスト用の動画で、候補探し（音の大きい区間が1位になる）と縦長の書き出し（1080x1920・15秒・冒頭テロップと字幕入り）を確認済み
