# 図解アニメの道具

- anim.html：アニメーションの本体（render(t) で時刻 t の画面を描く）
- render.js：1秒30コマで画面を撮影して frames/ に保存
- lines.json：ナレーションの文と長さ
- ナレーションは pyopenjtalk-plus（Open JTalk・HTS voice NIT ATR503 M001）。より自然な声にする場合は VOICEVOX（クレジット表記が必要）
- 2026-11-25：自治体向け案件（クラウドワークス 13622672）応募用のサンプルを作成
- sbv2.py：より自然な声（Style-Bert-VITS2・JVNVモデル）でナレーションを作る。Python 3.12 の仮想環境で `pip install style-bert-vits2 pyopenjtalk-plus "setuptools<81"`、HF_HUB_DISABLE_XET=1。読み込んだモデルを .float() にしないとエラーになる
  - 声のモデル：litagin/style_bert_vits2_jvnv（JVNVコーパス、CC BY-SA 4.0）。動画には「音声：Style-Bert-VITS2（JVNV）」などの表記を入れる
