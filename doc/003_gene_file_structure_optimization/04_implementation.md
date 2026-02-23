# 実装結果: 遺伝子ファイル構造の all_genes.json 一括化

実装日: 2026-02-23

---

## 実施したTODO

- [x] `nazokake/gene/` を `nazokake/bk_gene/` としてバックアップ
- [x] マイグレーションスクリプト `migrate_genes.py` を作成・実行（000〜002の変換 + 個別md削除）
- [x] `migrate_genes.py` を削除（taviが手動削除）
- [x] `.claude/scripts/` ディレクトリを作成
- [x] `.claude/scripts/extract_genes.py` を作成
- [x] `.claude/agents/gene-generator-agent.md` を更新
- [x] `.claude/agents/gene-evaluator-agent.md` を更新
- [x] `CLAUDE.md` を更新

---

## 変更・作成・削除ファイル一覧

### 新規作成

| ファイル | 内容 |
|---------|------|
| `nazokake/bk_gene/` | 移行前の nazokake/gene/ のバックアップ（全3世代分） |
| `nazokake/gene/000/all_genes.json` | 000世代 20遺伝子を JSON 化 |
| `nazokake/gene/001/all_genes.json` | 001世代 100遺伝子を JSON 化 |
| `nazokake/gene/002/all_genes.json` | 002世代 100遺伝子を JSON 化 |
| `.claude/scripts/extract_genes.py` | gene_num を指定して all_genes.json から抽出するユーティリティ |

### 削除

| ファイル | 内容 |
|---------|------|
| `nazokake/gene/000/[0-9]*.md` | 個別遺伝子ファイル 20件 |
| `nazokake/gene/001/[0-9]*.md` | 個別遺伝子ファイル 100件 |
| `nazokake/gene/002/[0-9]*.md` | 個別遺伝子ファイル 100件 |
| `migrate_genes.py` | 一時マイグレーションスクリプト（taviが手動削除） |

### 更新

| ファイル | 変更内容 |
|---------|---------|
| `.claude/agents/gene-generator-agent.md` | 遺伝子ファイル構成を all_genes.json 方式に全面改修。親読み込みに extract_genes.py を使用。子生成を一括Write方式に変更。 |
| `.claude/agents/gene-evaluator-agent.md` | `cat *.md` (Bash) → `all_genes.json` の Read 1回に変更。 |
| `CLAUDE.md` | ディレクトリ構造の記述を all_genes.json / evaluation.md の2ファイル構成に更新。 |

---


(レビュー) gene-generator-agentに、"`gene_num`: 3桁前ゼロつき文字列" ってあるけど、3桁かどうかは、criteria.mdで指定した遺伝子数に依存するよね？これ固定で3桁ってかかないほうがいいんじゃない？



## 実装後のAPIコール数

| フェーズ | 旧設計 | 新設計 |
|---------|--------|--------|
| generator: 親読み込み | Read×21（evaluation.md+個別20件） | Read×1（evaluation.md）+ Bash×1（extract_genes.py） |
| generator: 子書き出し | Write×100 | Write×1（all_genes.json） |
| evaluator: 全遺伝子読み | Bash×1（cat *.md） | Read×1（all_genes.json） |
| evaluator: 結果書き出し | Write×1 | Write×1 |
| **1サイクル合計** | **≒ 123回** | **≒ 5回** |

---

## 実装メモ

### マイグレーション実行結果

```
nazokake/gene/000: 20 genes → all_genes.json
nazokake/gene/000: individual .md files deleted
nazokake/gene/001: 100 genes → all_genes.json
nazokake/gene/001: individual .md files deleted
nazokake/gene/002: 100 genes → all_genes.json
nazokake/gene/002: individual .md files deleted
```

frontmatter（generation, gene_num, gene_eval）は除外し、本文のみを content フィールドに格納した。

### extract_genes.py の使い方

```bash
python3 .claude/scripts/extract_genes.py nazokake/gene/002/all_genes.json 007 042 091
# 出力例:
# [007] 猫とかけまして、プログラマーとときます。その心は、どちらもバグを追いかけるでしょう
# [042] ...
# [091] ...
```
