# 遺伝子家系図ビジュアライザー 技術調査

## 目的

複数のgene_typeにまたがる遺伝子の親子関係（parentsフィールド）を、世代をまたいだ家系図として可視化するツールの設計調査。

---

## 1. データ構造の把握

### gene_typeの一覧（現時点）

| gene_type | 世代数 | 遺伝子数/世代 | 総ノード数 |
|-----------|--------|--------------|-----------|
| nazokake  | 000〜009 (10世代) | 000:20, 001〜009:100 | 920 |
| novel140  | 001〜005 (5世代) | 100 | 500 |
| novel140_2 | 001〜005 (5世代) | 100 | 500 |

### ディレクトリ構造

```
{gene_type}/
  criteria.md
  gene/
    {世代数}/
      all_genes.json    ← 可視化の入力データ
      evaluation.md     ← ランク情報（あれば活用可能）
```

### all_genes.json のスキーマ

```json
{
  "generation": "002",
  "genes": [
    {
      "gene_num": "001",
      "content": "物語本文...",
      "parents": ["036", "001"],   // 前世代の gene_num を参照
      "meta": {
        "symbols": ["シンボルA", "シンボルB"]
      }
    }
  ]
}
```

### グラフ構造の特性

- **グラフ種別**: DAG（有向非循環グラフ）。厳密には木ではない（複数の子が同じ親を持ちうる）
- **世代001の親**: 空配列 `[]`（初期個体群）。nazokakeは000世代が20個の種個体
- **エッジ方向**: 親 → 子（世代が進む方向）
- **ファンアウト**: 1つの遺伝子が複数の子に親として参照される可能性あり

### evaluation.md のスキーマ

```markdown
---
generation: 001
evaluated_at: 2026-03-03
---
| rank | gene_num |
|------|----------|
| 1    | 025      |
...
```

ランク情報は visualization に色やサイズで反映可能。

---

## 2. 可視化ライブラリ比較

### 候補

| ライブラリ | 500+ノード対応 | DAGレイアウト | インタラクティブ | サーバー不要 | 実装コスト |
|-----------|-------------|-------------|--------------|-----------|----------|
| Mermaid | × (限界あり) | ○ | × | ○ | 低 |
| Graphviz/DOT | △ (密集) | ○ | × | 要変換 | 中 |
| D3.js | ○ | 要自前実装 | ○ | ○ | 高 |
| **Cytoscape.js** | **○** | **○ (dagreプラグイン)** | **○** | **○** | **中** |
| vis.js (Network) | ○ | ○ | ○ | ○ | 中 |

### 推奨: Cytoscape.js + dagre レイアウト

**理由:**
- グラフ/ネットワーク可視化専用設計。500〜900ノードを実用的速度で処理可能
- `cytoscape-dagre` プラグインで世代単位の階層レイアウトを自動計算
- ノードクリックでコンテンツ表示、祖先・子孫のハイライトが容易
- CDN経由で単一HTMLに完結（インストール不要）
- `evaluation.md` のランクをノードの色・サイズにマッピング可能

---

## 3. 配信方式の比較（重要設計判断）

### Option A: 単一の動的HTMLファイル（プロジェクトルートに配置）

```
ga_on_ai/
  viewer.html          ← ここだけ
  nazokake/gene/...
  novel140_2/gene/...
```

**動作:** ブラウザのドロップダウンでgene_typeを切り替え → fetch()でJSONを読み込みグラフ再描画

**問題点:**
- `fetch()` は `file://` プロトコルでCORSエラーが発生する
- **ローカルHTTPサーバーが必要**（`python -m http.server` など）
- ユーザーがサーバー起動を忘れると動かない

### Option B: gene_typeごとにHTMLを生成

```
ga_on_ai/
  nazokake/family_tree.html    ← 生成ツールで作成
  novel140_2/family_tree.html  ← 生成ツールで作成
```

**動作:** 生成ツールがJSONを読んでデータをHTML内にインライン埋め込み → ダブルクリックで開くだけ

**利点:**
- サーバー不要、`file://` プロトコルで動作
- 各gene_typeが独立して自己完結

**欠点:**
- GAを回すたびに再生成が必要
- gene_typeをまたいだ比較はできない

### Option C: 単一HTMLにすべてのgene_typeデータをインライン埋め込み（推奨）

```
ga_on_ai/
  viewer.html          ← 生成ツールが全gene_typeのデータを埋め込んで生成
```

**動作:**
1. 生成スクリプト（Python）がすべてのgene_typeのJSONを読み込む
2. データをJavaScript変数としてHTML内に埋め込んで `viewer.html` を出力
3. ブラウザで開くとドロップダウンでgene_type切り替え可能
4. サーバー不要

**利点:**
- ダブルクリックで即起動（サーバー不要）
- 複数gene_typeをドロップダウンで切り替え可能
- GAを回した後に生成スクリプトを再実行するだけで更新

**欠点:**
- データが大きい場合はHTMLが肥大化（nazokake 920ノード + 他で数MB程度、許容範囲）

---

## 4. 推奨アーキテクチャ

### 構成

```
ga_on_ai/
  tools/
    generate_viewer.py   ← 生成スクリプト
  viewer.html            ← 出力（gitignore推奨）
```

### 生成スクリプトの処理フロー

```
1. ルートディレクトリを走査し、criteria.md を持つディレクトリをgene_typeとして検出
2. 各gene_typeの gene/{世代}/all_genes.json を全世代読み込み
3. 各gene_typeの gene/{世代}/evaluation.md があればランク情報も読み込み
4. Cytoscape.js用のノード・エッジデータに変換
   - ノードID: "{gene_type}__{generation}__{gene_num}"
   - エッジ: 親ノードID → 子ノードID
5. データをJSON.stringifyしてHTMLテンプレートに埋め込み
6. viewer.html を出力
```

### 可視化UIの機能

- **gene_typeドロップダウン**: 切り替えでグラフ再描画
- **世代カラーコーディング**: 世代ごとに異なる色
- **ランクによるノードサイズ**: evaluation.mdのランクを反映（上位ほど大きい）
- **クリックでコンテンツ表示**: ノード選択でサイドパネルにcontent・parents・meta表示
- **祖先/子孫ハイライト**: 選択ノードの系譜を強調表示

---

## 5. 実装上の注意点

### パフォーマンス

- nazokake: 920ノード、エッジ数 ≈ 900×2 = 1800本 → Cytoscape.jsで問題なし
- dagre レイアウト計算は初回のみ、gene_type切り替え時に再計算
- 必要なら世代フィルタリングUI（「001〜003世代だけ表示」）を追加可能

### 世代間のエッジ解決

`parents` フィールドは前世代の `gene_num` を参照する。エッジ生成時は「現世代の遺伝子Nの親は、前世代のgene_num M」として解決する。

```python
# エッジ生成例
for gene in current_gen_genes:
    for parent_num in gene["parents"]:
        edge = {
            "source": f"{gene_type}__{prev_gen}__{parent_num}",
            "target": f"{gene_type}__{current_gen}__{gene['gene_num']}"
        }
```

### gene_typeの自動検出条件

`criteria.md` が存在し、かつ `gene/` サブディレクトリがあるディレクトリをgene_typeとして扱う。

---

## 6. 結論と推奨

**Option C（全データ埋め込み単一HTML）を推奨する。**

- 最もシンプルな運用（スクリプト実行 → HTMLをダブルクリック）
- サーバー不要
- gene_typeをまたいだ動的切り替えが可能
- 生成スクリプトはPython単体で実装可能（外部依存なし）
- Cytoscape.jsはCDN経由で調達、インターネット接続のみ必要

実装は `tools/generate_viewer.py` + `viewer.html` テンプレートの2ファイル構成が妥当。
