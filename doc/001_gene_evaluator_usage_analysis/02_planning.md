# 改善計画: gene-evaluator 高Usage削減（案B + 案C）

計画日: 2026-02-21

---

## アプローチ概要

**案B（評価結果を別ファイルに分離）＋ 案C（Bashで一括読み込み）の組み合わせ**

| 項目 | 現状 | 改善後 |
|------|------|--------|
| 遺伝子の読み込み | Read × 100回 | Bash 1回（cat *.md） |
| 評価結果の書き込み | Write × 100回（各ファイルに書き込み） | Write 1回（evaluation.mdに一括） |
| 合計ツール呼び出し | 200回以上 | 約2〜3回 |

---

## 変更するファイル

| ファイル | 変更内容 |
|----------|----------|
| `.claude/skills/gene-evaluator/SKILL.md` | Workflowを全面改修 |
| `.claude/skills/gene-generator/SKILL.md` | evaluation.mdを参照するよう変更 |
| `.claude/skills/gene-evaluator/template.md` | `gene_eval` 項目を削除 |
| `.claude/skills/gene-generator/template.md` | `gene_eval` 項目を削除 |

## 作成されるファイル（実装時・実行時）

```
gene/
  000/
    evaluation.md      ← 今回の実装で作成（既存世代の評価結果を生成）
  001/
    evaluation.md      ← 今回の実装で作成
  002/
    evaluation.md      ← 今回の実装で作成
  003/（以降の世代）
    001.md 〜 100.md   ← gene_eval フィールドなし（テンプレート変更後）
    evaluation.md      ← gene-evaluator実行時に作成
```

---

## 各ファイルの変更詳細

### 1. template.md の変更（gene-evaluator / gene-generator 共通）

**変更前：**
```yaml
---
generation: {世代数}
gene_num: {同一世代の中の連番}
gene_eval: {遺伝子の評価ランク}
---

{遺伝子の中身}
```

**変更後：**
```yaml
---
generation: {世代数}
gene_num: {同一世代の中の連番}
---

{遺伝子の中身}
```

- 既存の遺伝子ファイル（000〜002）は変更しない。`gene_eval` フィールドは残ったままでよい。
- 今後作成される遺伝子ファイルにはこのテンプレートが使われるため、`gene_eval` は含まれない。

### 2. gene-evaluator/SKILL.md のWorkflow変更

**変更前（現状）：**
```
1. 現世代のディレクトリの確認
2. 現世代を一つ一つ評価（Read × 100）
3. 現世代の遺伝子ファイルを更新（Write × 100）
```

**変更後：**
```
1. 現世代のディレクトリの確認
2. Bashで全ファイルを一括取得
3. 取得した内容をまとめて評価し、ランキングを決定
4. evaluation.md に一括書き込み（Write × 1）
```

Bashコマンドのイメージ：
```bash
cat gene/001/*.md
```

### 3. evaluation.md のフォーマット設計

```markdown
---
generation: 001
evaluated_at: 2026-02-21
---

| rank | gene_num |
|------|----------|
| 1    | 042      |
| 2    | 017      |
| 3    | 083      |
...（世代内の全遺伝子数分）
```

- 遺伝子の内容は書かない（個別ファイルに残っているため）
- ランク順に並べる
- gene-generatorが上位20件を取得しやすいシンプルな構造にする

### 4. gene-generator/SKILL.md の変更

**Step 3「上位20個の抽出」の変更：**

変更前：
```
現世代の全ファイルをチェックし、
遺伝子の評価ランクが1〜20になっているファイルを選ぶ
```

変更後：
```
gene/XXX/evaluation.md を1回Readし、
ランク1〜20のgene_numを取得する
```

Read回数が100回 → 1回になる。

---

## TODOリスト

- [ ] `.claude/skills/gene-evaluator/template.md` から `gene_eval` を削除
- [ ] `.claude/skills/gene-generator/template.md` から `gene_eval` を削除
- [ ] `.claude/skills/gene-evaluator/SKILL.md` のWorkflowを書き直す
  - Bash一括読み込みの手順を追加
  - evaluation.mdへの一括Writeの手順を追加
  - 個別ファイルへのWriteを削除
  - evaluation.md のフォーマットをSKILL.md内に明記する
- [ ] `.claude/skills/gene-generator/SKILL.md` のStep3を書き直す
  - evaluation.mdをReadする手順に変更
- [ ] 既存世代（000, 001, 002）の `evaluation.md` を作成する
  - `cat gene/XXX/*.md` で一括読み込み → ランク付け → evaluation.md を Write

---

## デメリット・限界

| 項目 | 内容 |
|------|------|
| Bash出力のサイズ | cat *.md の出力が全部コンテキストに入る。100ファイル × 数行なので現状問題ないが、遺伝子が長くなると将来的に増大する |
| evaluation.mdが壊れた場合 | 単一ファイルに依存するため、ファイルが欠損・破損すると全ランキングが失われる |
| 評価の途中経過が見えない | 現在は各ファイルに書き込むため進捗が見えるが、改善後は最後のWriteまで何も書かれない |
