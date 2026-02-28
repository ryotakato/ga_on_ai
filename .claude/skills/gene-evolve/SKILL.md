---
name: gene-evolve
description: |
  This skill should be used when the user asks to "進化させて", "次世代を生み出して", "GAを回して",
  "生成だけして", "評価だけして"
allowed-tools: Read, Task
---

# Gene Evolve（オーケストレーター）

指定された遺伝子タイプの遺伝子を進化させる。生成のみ・評価のみ・フルサイクルを選択できる。

## 入力パラメータ

- `gene_type`: 遺伝子タイプ名。ユーザーのプロンプトから取得する（例: nazokake）
- `mode`: 動作モード。ユーザーの指示から判断する（後述）
- `criteria_path`: `{gene_type}/criteria.md`（自動的に決まる）
- `gene_dir`: `{gene_type}/gene`（自動的に決まる）

## 動作モード

| モード | 説明 | ユーザーの指示例 |
|--------|------|----------------|
| `full`（デフォルト） | 生成 → 評価の1フルサイクル | 「進化させて」「GAを回して」 |
| `generate-only` | 生成のみ（評価はしない） | 「生成だけして」「次世代だけ作って」 |
| `evaluate-only` | 評価のみ（生成はしない） | 「評価だけして」「今の世代を評価して」 |

モードが不明確な場合はユーザーに確認する。

## Workflow

### 1. パラメータの決定

ユーザーの指示から `gene_type` と `mode` を取得する。
- `gene_type` が不明なら確認する
- `mode` が不明なら `full` とみなす

### 2. criteria.md の読み込み

`{gene_type}/criteria.md` を Read する。
YAMLフロントマターから以下を取得する：
- `initial_count`
- `selection_count`
- `offspring_count`

### 3. セクションの分割

読み込んだ内容から：
- `## crossbreeding` セクションの本文を取り出す
- `## evaluation` セクションの本文を取り出す

### 4. Generatorサブエージェントの起動（mode が full または generate-only の場合）

Task tool で gene-generator-agent を起動する。
プロンプトには以下を含める（evaluation は含めない）：

```
gene_dir: {gene_type}/gene
crossbreeding_criteria: {crossbreeding セクションの本文}
initial_count: {initial_count}
selection_count: {selection_count}
offspring_count: {offspring_count}
```

**注意: プロンプトにファイルフォーマットや出力形式を追加してはならない。フォーマットはサブエージェント自身が定義を持っている。**

完了するまで待つ。

### 5. Evaluatorサブエージェントの起動（mode が full または evaluate-only の場合）

Task tool で gene-evaluator-agent を起動する。
プロンプトには以下を含める（crossbreeding は含めない）：

```
gene_dir: {gene_type}/gene
evaluation_criteria: {evaluation セクションの本文}
```

完了するまで待つ。

### 6. 完了報告

実行したモードと、生成/評価した世代番号を報告する。
