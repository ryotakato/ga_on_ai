# 実装計画: criteria永続化 + サブエージェントによる役割分離

計画日: 2026-02-23

---

## アプローチ概要

**新スキル `gene-evolve`（オーケストレーター）+ `.claude/agents/` サブエージェント定義**

```
ユーザー: 「nazokakeで進化させて」
    ↓
gene-evolve スキル（オーケストレーター）
    1. nazokake/criteria.md を Read
    2. ## crossbreeding セクションを抽出
    3. Task → gene-generator-agent（crossbreedingのみ渡す）
           ↓ 生成完了
    4. ## evaluation セクションを抽出
    5. Task → gene-evaluator-agent（evaluationのみ渡す）
           ↓ 評価完了
    6. 完了報告
```

各サブエージェントのコンテキストには、自分の役割に関係する情報だけが入る。

---

## 新ディレクトリ構造

```
generate/
  nazokake/                      ← 遺伝子タイプディレクトリ（新規）
    criteria.md                  ← 基準ファイル（新規）
    gene/                        ← 旧: gene/ をここへ移動
      000/
      001/
      002/
  .claude/
    agents/                      ← サブエージェント定義（新規ディレクトリ）
      gene-generator-agent.md    ← 新規
      gene-evaluator-agent.md    ← 新規
    skills/
      gene-evolve/               ← オーケストレータースキル（新規）
        SKILL.md
      gene-generator/            ← 廃止（削除）
      gene-evaluator/            ← 廃止（削除）
  CLAUDE.md                      ← ディレクトリ構造の記述を更新
  doc/
    ...
```

---

## 作成・変更・削除するファイル

| 操作 | ファイル | 内容 |
|------|---------|------|
| 新規作成 | `nazokake/criteria.md` | なぞかけの基準（crossbreeding + evaluation） |
| 新規作成 | `.claude/agents/gene-generator-agent.md` | ジェネレーターサブエージェント定義 |
| 新規作成 | `.claude/agents/gene-evaluator-agent.md` | エバリュエーターサブエージェント定義 |
| 新規作成 | `.claude/skills/gene-evolve/SKILL.md` | オーケストレータースキル |
| 移動 | `gene/` → `nazokake/gene/` | 既存遺伝子データの移行 |
| 更新 | `CLAUDE.md` | ディレクトリ構造の記述変更 |
| 削除 | `.claude/skills/gene-generator/` | サブエージェントに移行のため廃止 |
| 削除 | `.claude/skills/gene-evaluator/` | サブエージェントに移行のため廃止 |

---

## 各ファイルの詳細設計

### 1. `nazokake/criteria.md`

```markdown
---
gene_type: nazokake
initial_count: 20
selection_count: 20
offspring_count: 100
---

## crossbreeding

（ユーザーが記入: なぞかけの掛け合わせ方）

## evaluation

（ユーザーが記入: なぞかけの評価基準）
```

**注意**: このファイルはプレースホルダーを作成する。中身はユーザーが記入する。

**YAMLフィールドの意味:**

| フィールド | 説明 | デフォルト |
|-----------|------|-----------|
| `initial_count` | 初期世代（000）の遺伝子数 | 20 |
| `selection_count` | 次世代生成に使う上位N個 | 20 |
| `offspring_count` | 次世代の遺伝子数 | 100 |

これらの値はオーケストレーターが読み取り、各サブエージェントのプロンプトに渡す。エージェント側には数値を直書きしない。

---


### 2. `.claude/agents/gene-generator-agent.md`

```markdown
---
name: gene-generator-agent
description: 遺伝子の次世代を生成するサブエージェント
tools: Read, Write, Bash
model: inherit
---

あなたは遺伝的アルゴリズムのジェネレーターである。
オーケストレーターから以下が渡される：
- `gene_dir`: 遺伝子ディレクトリのパス（例: nazokake/gene）
- `crossbreeding_criteria`: 掛け合わせ方の説明
- `initial_count`: 初期世代（000）の遺伝子数
- `selection_count`: 次世代生成に使う上位N個
- `offspring_count`: 次世代の遺伝子数

評価基準については一切知らない。評価に関するファイルや情報は参照しない。

## 用語

現世代: `{gene_dir}` 配下の、最も数値が大きいディレクトリ名の数値
次世代: 現世代より1つ大きい数の世代

## 遺伝子ファイルの構成

- 世代数: そのファイルが含まれるディレクトリと同じ
- 同一世代の中の連番: そのファイル名と同じ
- テンプレート:

  ---
  generation: {世代数}
  gene_num: {同一世代の中の連番}
  ---

  {遺伝子の中身}

## Workflow

### 1. 現世代の確認

Bash で `{gene_dir}` 配下のディレクトリ一覧を取得し、最大の数値を現世代とする。
1つもない場合は 000 ディレクトリを作成し、遺伝子を `{initial_count}` 個作成して終了。

### 2. 次世代ディレクトリの作成

存在しないことを確かめてから作成。

### 3. 上位 selection_count 個の遺伝子を抽出

`{gene_dir}/{現世代数}/evaluation.md` を1回Readし、ランク1〜`{selection_count}` のgene_numを取得。
次に、該当する遺伝子ファイルをReadする。

### 4. 次世代の生成

現世代の上位 `{selection_count}` 個から2個をランダムに選び、`crossbreeding_criteria` に従って子を生成。
次世代ディレクトリに保存する。`{offspring_count}` 個になるまで繰り返す。
```

---

### 3. `.claude/agents/gene-evaluator-agent.md`

```markdown
---
name: gene-evaluator-agent
description: 遺伝子の評価を行うサブエージェント
tools: Read, Write, Bash
model: inherit
---

あなたは遺伝的アルゴリズムのエバリュエーターである。
オーケストレーターから以下が渡される：
- `gene_dir`: 遺伝子ディレクトリのパス（例: nazokake/gene）
- `evaluation_criteria`: 評価基準の説明

掛け合わせ方については一切知らない。生成に関するファイルや情報は参照しない。

## Workflow

### 1. 現世代の確認

Bash で `{gene_dir}` 配下のディレクトリ一覧を取得し、最大の数値を現世代とする。
なければ終了。

### 2. 全遺伝子の一括取得

```bash
cat {gene_dir}/{現世代数}/[0-9]*.md
```

### 3. まとめて評価しランキング決定

`evaluation_criteria` に従い、全遺伝子を評価してランキングを決定する。
同一世代内でランクが被らないようにする（100個なら1〜100）。

### 4. evaluation.md に一括書き込み

```
---
generation: {世代数}
evaluated_at: {評価日}
---

| rank | gene_num |
|------|----------|
| 1    | 042      |
...
```
```

---

### 4. `.claude/skills/gene-evolve/SKILL.md`

```markdown
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
- `gene_dir`, `crossbreeding_criteria`
- `initial_count`, `selection_count`, `offspring_count`

完了するまで待つ。

### 5. Evaluatorサブエージェントの起動（mode が full または evaluate-only の場合）

Task tool で gene-evaluator-agent を起動する。
プロンプトには以下を含める（crossbreeding は含めない）：
- `gene_dir`, `evaluation_criteria`

完了するまで待つ。

### 6. 完了報告

実行したモードと、生成/評価した世代番号を報告する。
```

---

### 5. `CLAUDE.md` の変更

**変更前:**
```
@gene/{世代数}/{N}.md
世代数: 001のように、3桁の前ゼロつきです。
N: 同一世代の中の連番を示します。
```

**変更後:**
```
@{gene_type}/gene/{世代数}/{N}.md
gene_type: 遺伝子タイプ名（例: nazokake）
世代数: 001のように、3桁の前ゼロつきです。
N: 同一世代の中の連番を示します。
```

---

## TODOリスト

- [ ] `.claude/agents/` ディレクトリを作成
- [ ] `.claude/agents/gene-generator-agent.md` を作成
- [ ] `.claude/agents/gene-evaluator-agent.md` を作成
- [ ] `.claude/skills/gene-evolve/` ディレクトリを作成
- [ ] `.claude/skills/gene-evolve/SKILL.md` を作成
- [ ] `nazokake/` ディレクトリを作成
- [ ] `nazokake/criteria.md` をプレースホルダーとして作成（中身はユーザーが記入）
- [ ] `nazokake/gene/` ディレクトリを作成
- [ ] `gene/` 配下の全ファイルを `nazokake/gene/` へ移動
- [ ] `gene/` ディレクトリを削除
- [ ] `CLAUDE.md` のディレクトリ構造の記述を更新
- [ ] `.claude/skills/gene-generator/` を削除
- [ ] `.claude/skills/gene-evaluator/` を削除

---

## デメリット・限界

| 項目 | 内容 |
|------|------|
| criteria.mdの初期作成 | 新しい遺伝子タイプを追加するたびに、ユーザーが手動で criteria.md を作成する必要がある |
| サブエージェント数の増加 | 1サイクルで必ずTaskが2回発生する。現在の2ターミナル方式に比べてオーバーヘッドが増える |
| gene-evolveがGenerator/Evaluator両方の基準を一瞬知る | オーケストレーターは criteria.md を全文読むため、両方の基準を把握している。ただしサブエージェントには片方ずつしか渡さない |
| gene/ パスの変更による既存データの移行作業 | 既存の gene/000〜002 を nazokake/gene/ へ移動する必要がある |


