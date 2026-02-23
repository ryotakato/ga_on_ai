# 実装結果: gene-evaluator 高Usage削減

実装日: 2026-02-21

---

## 実装したTODO

- [x] `.claude/skills/gene-evaluator/template.md` から `gene_eval` を削除
- [x] `.claude/skills/gene-generator/template.md` から `gene_eval` を削除
- [x] `.claude/skills/gene-evaluator/SKILL.md` のWorkflowを書き直す
- [x] `.claude/skills/gene-generator/SKILL.md` のStep3を書き直す
- [x] 既存世代（000, 001, 002）の `evaluation.md` を作成する

---

## 変更・作成ファイル一覧

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `.claude/skills/gene-evaluator/template.md` | `gene_eval` フィールドを削除 |
| `.claude/skills/gene-generator/template.md` | `gene_eval` フィールドを削除 |
| `.claude/skills/gene-evaluator/SKILL.md` | Workflow全面改修（Bash一括読み込み + evaluation.md 一括書き込み） |
| `.claude/skills/gene-generator/SKILL.md` | Step3をevaluation.md参照に変更 |

### 新規作成ファイル

| ファイル | 内容 |
|----------|------|
| `gene/000/evaluation.md` | 世代000の評価結果（20件、ランク順） |
| `gene/001/evaluation.md` | 世代001の評価結果（100件、ランク順） |
| `gene/002/evaluation.md` | 世代002の評価結果（100件、ランク順） |

---

## 実装メモ

### 既存世代の evaluation.md 作成について

既存の遺伝子ファイルに `gene_eval` フィールドが入っていたため、
Bashスクリプトでそれを活用して evaluation.md を生成した。

```bash
for f in gene/$gen/[0-9]*.md; do
  num=$(grep "^gene_num:" "$f" | awk '{print $2}')
  eval=$(grep "^gene_eval:" "$f" | awk '{print $2}')
  echo "$eval $num"
done | sort -n
```

`[0-9]*.md` のパターンを使うことで evaluation.md 自身を除外している。

### gene_eval フィールドについて

- 既存の遺伝子ファイル（000〜002）の `gene_eval` フィールドはそのまま残す（変更しない）
- テンプレートから削除したため、今後作成される遺伝子ファイルには含まれない

### SKILL.md のWorkflow変更ポイント

**gene-evaluator**: 100回のRead/Writeが、Bash1回+Write1回に削減された

| ステップ | 変更前 | 変更後 |
|----------|--------|--------|
| 全遺伝子の読み込み | Read × N回 | `cat gene/XXX/[0-9]*.md` のBash 1回 |
| 評価結果の書き込み | Write × N回（各ファイルへ） | `evaluation.md` へのWrite 1回 |

**gene-generator**: Step3の上位抽出が100回Readから1回Readに削減された

| ステップ | 変更前 | 変更後 |
|----------|--------|--------|
| 上位20件の取得 | 全ファイルをRead × 100回 | `evaluation.md` をRead 1回 |
