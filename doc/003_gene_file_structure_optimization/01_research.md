# 調査レポート: 遺伝子ファイル構造の最適化

調査日: 2026-02-23

---

## 1. 検討した案と結論の概要

| 案 | 内容 | 結論 |
|----|------|------|
| A: criteria.mdをサブエージェント用に2ファイルに分割 | crossbreeding.mdとevaluation.mdに事前分割 | **不採用**: トークン削減にならず、情報分離も弱体化 |
| B: 遺伝子を all_genes.json に一括管理 | 個別.mdファイルをやめ、世代ごとに1つのJSONにまとめる | **採用**: APIコール数を大幅削減 |

---

## 2. 案A: criteria.md の事前ファイル分割

### 提案の意図

criteria.md（crossbreeding + evaluation の両セクションを含む）を、サブエージェントに渡す前に：

```
nazokake/crossbreeding.md  ← generator用
nazokake/evaluation.md     ← evaluator用
```

に分割しておけば、毎サイクルのTaskプロンプトにcriteria本文を含めず、ファイルパスだけ渡せてトークン節約になるのでは？という発想。

### 分析結果

**トークン効率の観点:**

| 方式 | サブエージェントのコンテキスト |
|------|-------------------------------|
| プロンプトに直接渡す | 200トークン（初期から存在） |
| ファイルを読む | 20トークン（初期）+ Read 1回 + 200トークン（ツール結果）= 合計220トークン+ 1APIコール |

サブエージェントが最終的に処理するトークン数はほぼ同じか、ファイル方式の方がむしろ多い。プロンプト渡しの方がRead 1回分少ない。

**情報分離の観点:**

ファイルとしてディスク上に存在してしまうため、generator が evaluation.md を「読まない」保証は指示依存になる（軟分離）。現在のプロンプト直接渡し方式は、ファイルが存在しないため構造的に分離されている（強分離）。

**結論: 不採用**

- トークン削減効果なし（むしろ微増）
- 情報分離が強分離→軟分離に後退
- 現行のプロンプト直接渡しを維持する

---

## 3. 案B: 遺伝子の一括JSON管理（all_genes.json）

### 提案の背景

現行設計では、generatorが次世代100個の遺伝子ファイルを個別にWriteするため、**Write × 100回 = 100 APIコール**が発生する。これをまとめる方法として検討。

### 設計

**generatorが書くもの:**

```
nazokake/gene/{世代数}/all_genes.json
```

```json
{
  "generation": "003",
  "genes": [
    {"gene_num": "001", "content": "算数とかけまして..."},
    {"gene_num": "002", "content": "橋とかけまして..."},
    ...（offspring_count 個分）
  ]
}
```

Write 1回で完結。

**evaluatorが読むもの:**

```
nazokake/gene/{世代数}/all_genes.json  ← 1回のReadで全遺伝子を取得
→ evaluation.md を書く                ← 1回のWrite
```

個別ファイルを `cat *.md` で読んでいた既存の方式（Bash 1回）と同等だが、JSONの方が構造化されており扱いやすい。

**次世代generatorの親読み込み:**

```
nazokake/gene/{現世代}/evaluation.md     ← ランキング取得（1 Read）
nazokake/gene/{現世代}/all_genes.json    ← 上位selection_count個の中身を取得（1 Read）
```

evaluation.md のランキングを参照してgene_numを特定し、all_genes.json から対応するcontentを取得する。個別ファイルへのReadが不要になる。

### APIコール数の比較

| フェーズ | 旧設計（個別.mdファイル） | 新設計（all_genes.json） |
|---------|--------------------------|------------------------|
| generator: 親読み込み | evaluation.md(1) + 個別ファイル(20) = 21回 | evaluation.md(1) + all_genes.json(1) = 2回 |
| generator: 子書き出し | Write × 100回 | Write × 1回 |
| evaluator: 全遺伝子読み | Bash cat *.md（1回） | Read all_genes.json（1回） |
| evaluator: 結果書き出し | Write × 1回 | Write × 1回 |
| **1サイクル合計** | **≒ 123回** | **≒ 5回** |

### 失うもの

- 個別の `.md` ファイルがなくなるため、特定の遺伝子を目視確認しにくくなる
- CLAUDE.md のディレクトリ構造記述の更新が必要

### 結論: 採用

APIコール数を 123回 → 5回 に削減できる。個別ファイルの廃止というトレードオフはあるが、効率化の効果が大きく上回る。

---

## 4. 変更が必要な箇所（次フェーズ: プランニングで詳細化）

| 対象 | 変更内容 |
|------|---------|
| `gene-generator-agent.md` | 子の書き出しをall_genes.json 1回のWriteに変更。親の読み込みもall_genes.jsonから |
| `gene-evaluator-agent.md` | `cat *.md` → `all_genes.json` のReadに変更 |
| `CLAUDE.md` | ディレクトリ構造の記述を更新（個別ファイル → all_genes.json） |
| 既存遺伝子データ（000〜002） | 個別.mdファイルのまま残す（移行は不要。過去世代は読み取りのみ） |
