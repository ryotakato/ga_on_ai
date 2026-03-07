# 遺伝子家系図ビジュアライザー 実装計画

調査結果: `doc/007_gene_family_tree_visualizer/01_research.md` 参照

---

## アプローチ概要

**Option B 改: gene_typeごとにHTMLを生成 + ライブラリをローカルにインライン埋め込み**

当初のOption C（全gene_typeを1つのHTMLに集約）から方針を変更する。

**変更理由:**
- gene_typeが増えると1つのHTMLが際限なく肥大化する
- CDN依存はオフライン環境やネットワーク遅延のリスクがある

**新方針:**
- 各gene_typeに対して独立した `family_tree.html` を生成する（スケールしやすい）
- Cytoscape.js等のライブラリはあらかじめ `tools/vendor/` にダウンロードしておき、生成時にHTMLへインライン埋め込みする（オフライン・完全自己完結）

```
[初回セットアップ]
tools/download_libs.py → tools/vendor/{cytoscape,dagre,...}.min.js をダウンロード

[HTML生成（毎回）]
tools/generate_viewer.py novel140_2
  → novel140_2/gene/*/all_genes.json + evaluation.md を読み込み
  → tools/vendor/ のJSをインライン埋め込み
  → novel140_2/family_tree.html を出力（ダブルクリックで開くだけ）

tools/generate_viewer.py  ← 引数なしで全gene_typeを一括生成
```

---

## ファイル構成

```
ga_on_ai/
  tools/
    download_libs.py       ← 新規作成（ライブラリ初回ダウンロード用）
    generate_viewer.py     ← 新規作成（HTML生成スクリプト）
    vendor/
      cytoscape.min.js     ← ダウンロード済みライブラリ（gitignore推奨）
      dagre.min.js
      cytoscape-dagre.min.js
  nazokake/
    family_tree.html       ← 生成出力（gitignore推奨）
  novel140/
    family_tree.html       ← 生成出力（gitignore推奨）
  novel140_2/
    family_tree.html       ← 生成出力（gitignore推奨）
  .gitignore               ← family_tree.html と tools/vendor/ を追記
```

---

## 各スクリプトの設計

### download_libs.py（初回1回だけ実行）

```python
# 以下の3ファイルを tools/vendor/ にダウンロードする
LIBS = {
    "cytoscape.min.js":        "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js",
    "dagre.min.js":            "https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js",
    "cytoscape-dagre.min.js":  "https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js",
}
# urllib.request のみ使用（外部ライブラリ不要）
```

### generate_viewer.py の処理フロー

```python
# 引数: gene_type名（省略時は全gene_typeを処理）
# python tools/generate_viewer.py novel140_2
# python tools/generate_viewer.py           ← 全件

# 1. gene_type の特定（引数 or 自動検出）
#    自動検出条件: criteria.md + gene/ の両方が存在するディレクトリ

# 2. tools/vendor/ のJSを読み込んでおく（インライン埋め込み用）
js_inline = read("tools/vendor/cytoscape.min.js") + ...

# 3. 対象 gene_type のデータ収集
for each generation (sorted):
    genes = load_json(f"{gene_type}/gene/{gen}/all_genes.json")
    ranks = parse_evaluation_md(f"{gene_type}/gene/{gen}/evaluation.md")  # なければスキップ

# 4. Cytoscape.js 用ノード・エッジ変換
#    ノードID: "{generation}__{gene_num}"（1ファイル内なので gene_type prefix 不要）
nodes = [{ "data": { "id": "002__001", "generation": "002", "gene_num": "001",
                     "content": "...", "symbols": [...], "rank": 5 } }]
edges = [{ "data": { "source": "001__036", "target": "002__001" } }]

# 5. HTMLテンプレートにデータを埋め込んで出力
html = TEMPLATE
    .replace("__GRAPH_DATA__", json.dumps({"nodes": nodes, "edges": edges}))
    .replace("__GENE_TYPE__", gene_type)
write(f"{gene_type}/family_tree.html", html)
```


### evaluation.md のパース方法

**用途:** ノードのスタイリングにランク情報を反映するため。上位ランクの遺伝子を大きく・目立つ色で表示することで、「どの系譜が優秀な遺伝子を生んだか」が視覚的にわかる。

frontmatterは読み飛ばし、Markdownテーブルの `rank` と `gene_num` 列だけ正規表現で抽出する。ファイルが存在しない場合はスキップ（rank = None）。全ノードを同サイズ・同色で表示する。

---

## viewer.html の設計

### 使用ライブラリ（相対パス参照）

CDNは使用しない。`tools/vendor/` に事前ダウンロード済みのJSを相対パスで参照する。

`<script src>` による相対パス参照は `file://` プロトコルでもCORSの制限なく動作する（`fetch()` とは異なる）。インライン埋め込みは不要。

```html
<!-- {gene_type}/family_tree.html から見た相対パス -->
<script src="../tools/vendor/cytoscape.min.js"></script>
<script src="../tools/vendor/dagre.min.js"></script>
<script src="../tools/vendor/cytoscape-dagre.min.js"></script>
```

これにより：
- HTMLファイルは軽量（データのみ）
- ライブラリは全gene_typeのHTMLで共有される
- ネットワーク接続なしで完全動作

### UI レイアウト

```
┌─────────────────────────────────────────────────┐
│ [gene_type ▼]  [世代フィルタ: 全て ▼]  [リセット]  │  ← ヘッダー
├───────────────────────────────┬─────────────────┤
│                               │  ノード詳細      │
│     Cytoscape グラフ領域       │  gene_num: 001  │
│                               │  世代: 002      │
│  ノードをクリックで詳細表示     │  content: ...   │
│                               │  parents: ...   │
│                               │  rank: 5        │
└───────────────────────────────┴─────────────────┘
```

### ノードのスタイリング

| 要素 | ルール |
|------|--------|
| ノード色 | 世代ごとに異なるカラーパレット（最大10世代分） |
| ノードサイズ | rankがある場合: 上位20件は大きめ、それ以外は標準 |
| 選択時 | 黄色ボーダー + 祖先・子孫エッジを強調 |
| ホバー時 | ツールチップでgene_numと世代を表示 |

### Cytoscape レイアウト設定

```javascript
cy.layout({
    name: 'dagre',
    rankDir: 'TB',       // 上から下（世代順）
    nodeSep: 30,
    rankSep: 80,
    animate: false       // 500+ノードでアニメOFFが無難
}).run();
```

### gene_type 切り替え処理

各HTMLは1つのgene_type専用のため、切り替えUIは不要。ページタイトルにgene_type名を表示するだけでよい。世代フィルタリングUIは引き続き保持する。

---

## デメリット・限界

- **初回セットアップが必要**: `download_libs.py` を一度だけ実行してライブラリをダウンロードする必要がある（以降はオフライン完結）
- **HTMLが `tools/vendor/` に依存する**: 相対パス参照のため、HTMLファイル単体をプロジェクト外に持ち出すと動かない。プロジェクト内で使う限り問題なし
- **GAを回すたびに再生成が必要**: family_tree.htmlは静的スナップショット。新しい世代が追加されたら `generate_viewer.py` を再実行する
- **nazokakeの920ノードでは密集する**: dagreの自動レイアウトは縦方向に並ぶが、横方向に100ノードが並ぶため横スクロールが広大になる可能性がある
  - 対策: 世代フィルタリングUIで表示範囲を絞れるようにする
- **gene_typeをまたいだ比較はできない**: 各HTMLが独立しているため、複数gene_typeの横断比較は非対応（現時点では不要と判断）

---

## TODO リスト

- [ ] `tools/download_libs.py` を作成
  - [ ] cytoscape.min.js / dagre.min.js / cytoscape-dagre.min.js を `tools/vendor/` にダウンロード
- [ ] `tools/generate_viewer.py` を作成
  - [ ] 引数パース（gene_type名 or 省略で全件）
  - [ ] gene_type 自動検出ロジック（criteria.md + gene/ の存在チェック）
  - [ ] 全世代の `all_genes.json` 読み込み
  - [ ] `evaluation.md` のパース（rank抽出）
  - [ ] Cytoscape.js用ノード・エッジデータへの変換
  - [ ] HTMLテンプレート文字列（generate_viewer.py内にインライン定義）
  - [ ] `{gene_type}/family_tree.html` の出力
- [ ] HTMLテンプレートの実装
  - [ ] JSライブラリのインライン `<script>` プレースホルダー
  - [ ] 世代フィルタリングUI
  - [ ] Cytoscape.js 初期化 + dagre レイアウト
  - [ ] ノードスタイリング（世代色・rankサイズ）
  - [ ] クリックでサイドパネルに詳細表示
  - [ ] 祖先・子孫ハイライト
- [ ] `.gitignore` に `**/family_tree.html` と `tools/vendor/` を追記
- [ ] 動作確認: novel140_2（500ノード）、nazokake（920ノード）
