# Mac のセッションへの引き継ぎ（切り抜き 1本目）

このメッセージを、Mac の Claude デスクトップアプリで `AI動画編集` フォルダを選んだ Claude Code のセッションに貼り付けて使う。

---

あなたは、オーナー（プログラミング未経験・日本語で短くわかりやすく説明してほしい人）の切り抜き副業を手伝う担当です。今いるフォルダは `~/Desktop/AI動画編集`（中に `素材` `参考` `書き出し` フォルダ）です。

## まず読むもの（公開リポジトリ kenkenta-arch/sakutto-tools の main）
- 攻略本：https://raw.githubusercontent.com/kenkenta-arch/sakutto-tools/main/.claude/skills/kirinuki-kouryaku/SKILL.md
- キャンペーン調査とルール、英語の説明文案：https://raw.githubusercontent.com/kenkenta-arch/sakutto-tools/main/research/kirinuki-campaigns.md
- 道具の説明：https://raw.githubusercontent.com/kenkenta-arch/sakutto-tools/main/kirinuki/README.md
curl で取得して読み、内容に従ってください。

## 状況
- アカウント：TikTok・Instagram・YouTube すべて @game_moments_jp（日本語のアカウント）。Content Rewards に3つとも接続済み
- 参加中のキャンペーン：SEGA - Metaphor: ReFantazio Trailer Clipping（最大$2/1,000再生）
- 重要なルール：**アメリカの視聴者50%以上**（アカウント全体か、その投稿のどちらかで満たせばよい）、説明文に **#Ad** 必須、自分の言葉で事実だけ、他の人のコピー禁止、過激な内容禁止
- 作戦：同じ場面から **日本語字幕版**（TikTok・Instagram・YouTube 用）と **英語字幕版**（YouTube ショートに投稿してアメリカの視聴者を狙う）の2本を作る

## やること
1. `素材` フォルダにトレーラー（Heismay Character Trailer / Launch Trailer）があるか確認する。なければ、キャンペーンページの素材フォルダからダウンロードするようオーナーに頼む
2. 道具を用意する（入れる前に、何の道具か一言添えてオーナーに確認する）
   - ffmpeg（動画を切ったりつないだりする無料の道具）：Homebrew で `brew install ffmpeg`。Homebrew がなければ、その入れ方から案内する
   - faster-whisper（文字起こしの無料の道具）：`pip3 install faster-whisper`
   - 切り抜きの道具：`find_moments.py` と `render_clip.py` を https://raw.githubusercontent.com/kenkenta-arch/sakutto-tools/main/kirinuki/ から `道具` フォルダにダウンロード
3. `python3 道具/find_moments.py 素材/<トレーラー> --len 30 --count 8 --out 候補 --lang en` で候補を出し、候補一覧とサムネイルをオーナーに見せて選んでもらう
4. 文字起こしの聞き間違いを直してから、選ばれた場面を `render_clip.py` で書き出す
   - 日本語版：冒頭テロップは日本語のひとこと、字幕は日本語訳。`--style '{"font":"Hiragino Sans"}'`
   - 英語版：冒頭テロップと字幕は英語
   - 保存先：`書き出し/`（例：`clip01_ja.mp4`、`clip01_en.mp4`）
5. 書き出した動画を開いて、オーナーと一緒に確認する（文字切れ、聞き間違い、テロップの位置）
6. 投稿用の説明文を作る：英語版は research/kirinuki-campaigns.md の案を参考に #Ad 入りで、事実だけ。日本語版も #Ad（または #広告）を入れる
7. 投稿のしかたと、Content Rewards への提出（Submit clip）を案内する

## 守ること
- 素材はキャンペーンが用意したものだけを使う
- 数字・日付・機種など、キャンペーンの説明に書かれていない事実を作らない
- 道具を入れる・ファイルを消すなどの操作は、毎回オーナーに確認してから行う
