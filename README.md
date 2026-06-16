# バイクルート AI プランナー

125cc / 50cc バイク専用の **下道限定ツーリングプラン自動生成 Agent**

Claude AI（claude-haiku-4-5）が観光スポット・飲食店・ガソリンスタンドを沿道で自動検索し、  
時間配分アルゴリズムで厳密なタイムラインを生成します。

---

## 特徴

- **下道限定ルート** — OSRM で高速・自動車専用道を自動回避
- **時間配分アルゴリズム** — 移動時間・バッファ・食事を差し引いて景点数を動的計算
- **沿道POI自動検索** — OpenStreetMap (Overpass API) で景点・飲食店・GSを無料取得
- **50cc / 125cc 対応** — 排量別の速度設定（28km/h / 45km/h）
- **シネマティックUI** — SVGバイクシルエットのcinemaイントロ → 日本地図 → フォーム → 結果マップ

---

## アーキテクチャ

```
【Step 1】Nominatim   地名 → 緯度経度
【Step 2】OSRM        下道ルート + 距離取得
【Step 3】Pure Python  時間配分アルゴリズム（コア）
【Step 4】Overpass API 沿道POI検索
【Step 5】Claude AI    Markdownプラン生成
```

> **設計思想**: 確実に順番通りに実行すべき処理（ルート取得・時間計算）はPythonで直接呼び出し、  
> AIには「文章を読む・書く」という得意な部分だけを担当させる。

---

## ファイル構成

```
├── app_fastapi.py    # FastAPI バックエンド（GET / → index.html, POST /api/plan → Agent呼び出し）
├── agent.py          # Agent メインロジック（5ステップパイプライン）
├── tools.py          # 外部API の Tool 関数 + Claude tool 定義
├── planner.py        # 時間配分コアアルゴリズム（純Python）
├── config.py         # 設定値（速度・時間パラメータ・道路設定）
├── static/
│   └── index.html    # フロントエンド（cinemaアニメ・日本地図SVG・フォーム・Leaflet地図）
└── requirements.txt
```

---

## セットアップ

```bash
# 1. 仮想環境を作成
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# 2. 依存パッケージをインストール
pip install -r requirements.txt

# 3. APIキーを設定
cp .env.example .env
# .env を開いて ANTHROPIC_API_KEY を設定

# 4. 起動
uvicorn app_fastapi:app --reload --port 8000
```

→ http://localhost:8000 をブラウザで開く

---

## 使用API（全て無料）

| API | 用途 |
|-----|------|
| [Nominatim](https://nominatim.org/) | 地名 → 緯度経度 |
| [OSRM](https://project-osrm.org/) | 下道ルーティング |
| [Overpass API](https://overpass-api.de/) | POI検索（OSMデータ） |
| [Anthropic API](https://www.anthropic.com/) | AI文章生成（要APIキー） |

---

## 技術スタック

- **AI**: Claude Haiku 4.5（Anthropic）
- **バックエンド**: FastAPI + Python 3.11+
- **フロントエンド**: 純HTML / CSS / JavaScript
- **アニメーション**: GSAP 3 + SVG
- **地図**: Leaflet.js（CartoDB Dark Matter タイル）
