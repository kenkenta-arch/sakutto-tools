# 図解アニメの道具

- anim.html：アニメーションの本体（render(t) で時刻 t の画面を描く）
- render.js：1秒30コマで画面を撮影して frames/ に保存
- lines.json：ナレーションの文と長さ
- ナレーションは pyopenjtalk-plus（Open JTalk・HTS voice NIT ATR503 M001）。より自然な声にする場合は VOICEVOX（クレジット表記が必要）
- 2026-11-25：自治体向け案件（クラウドワークス 13622672）応募用のサンプルを作成
