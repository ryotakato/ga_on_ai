# 遺伝子家系図ビジュアライザー 実装結果

## 作成・変更ファイル一覧

| 操作 | ファイル |
|------|---------|
| 新規作成 | `tools/download_libs.py` |
| 新規作成 | `tools/generate_viewer.py` |
| 変更 | `.gitignore` |
| 生成出力 (gitignore済) | `tools/vendor/cytoscape.min.js` |
| 生成出力 (gitignore済) | `tools/vendor/dagre.min.js` |
| 生成出力 (gitignore済) | `tools/vendor/cytoscape-dagre.min.js` |
| 生成出力 (gitignore済) | `nazokake/family_tree.html` |
| 生成出力 (gitignore済) | `novel140/family_tree.html` |
| 生成出力 (gitignore済) | `novel140_2/family_tree.html` |

---

## 動作確認結果

```
detected gene_types: ['nazokake', 'novel140', 'novel140_2']
  nazokake   : 920 nodes,   0 edges
  novel140   : 500 nodes, 200 edges
  novel140_2 : 500 nodes, 800 edges
```

---

## 実装中に気づいたこと・対処

### 1. nazokake は旧フォーマット（parents フィールドなし）

nazokake の全世代の遺伝子に `parents` フィールド自体が存在しない旧フォーマット。
`gene.get("parents", [])` でデフォルト空配列として扱い、エッジなしでノードのみ表示される。
これは仕様通りの正常動作。

### 2. novel140 の gen003〜005 は `parents: null`

`parents` フィールドは存在するが値が `null`。`gene.get("parents", [])` では `None` が返り
イテレーション時にエラーが発生する。`gene.get("parents") or []` に修正して対処した。

---

## 使い方

### 初回セットアップ（1回だけ）

```bash
python tools/download_libs.py
```

`tools/vendor/` にライブラリが保存される。

### HTML 生成

```bash
python tools/generate_viewer.py              # 全 gene_type を一括生成
python tools/generate_viewer.py novel140_2   # 指定した gene_type のみ
```

### 閲覧

```bash
open novel140_2/family_tree.html  # macOS
# または各 gene_type ディレクトリの family_tree.html をダブルクリック
```


(注釈)HTMLをブラウザで確認した。操作性の問題として、マウスの横方向の動きでズームされるのがいや。これなんとかできないものか？
(注釈)予想はしていたけど、1世代100ノードもあると、かなり横に広いグラフになるね。これ縦方向つまり世代間をもう少し広くして、かつ横方向をほんの少しだけ狭くすることはできる？

(注釈)縦方向はさらに2倍ぐらいあってもいい。
(注釈)移動が左クリックした状態でマウス動かさないといけないってのが操作性が悪い。逆に左クリックしているときだけはズームで、普通は移動ってことはできない？

(注釈)nodeSepは8で、rankSepは1100でお願い。

### フィードバック対応まとめ（generate_viewer.py を修正）

| 指摘 | 対応内容 |
|------|---------|
| 横スクロールでズームされる | ホイールイベントを全面乗っ取り。横スクロール → パン、Ctrl/ピンチ → ズームに変更 |
| 左クリックドラッグでしか移動できない | 上記と同じ対応。スクロールでパンできるようになったため操作性改善 |
| 縦方向（世代間）を広くしたい | `rankSep: 70 → 110 → 220 → 1100` |
| 横方向をもう少し狭くしたい | `nodeSep: 25 → 12 → 8` |

### 新しい gene_type を追加した場合

`criteria.md` と `gene/` ディレクトリがあれば自動検出される。
