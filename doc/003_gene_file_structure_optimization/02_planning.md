# 実装計画: 遺伝子ファイル構造の all_genes.json 一括化

計画日: 2026-02-23

---

## アプローチ概要

世代ごとの個別 `.md` ファイルを廃止し、`all_genes.json` に一括管理する。
既存世代（000〜002）はマイグレーションスクリプトで変換する。

```
変更前:
  nazokake/gene/002/
    001.md, 002.md, ... 100.md   ← 100ファイル
    evaluation.md

変更後:
  nazokake/gene/002/
    all_genes.json               ← 1ファイル
    evaluation.md
```

---

## all_genes.json フォーマット

```json
{
  "generation": "002",
  "genes": [
    {"gene_num": "001", "content": "猫とかけまして、プログラマーとときます。その心は、どちらも切れ味が大事でしょう"},
    {"gene_num": "002", "content": "橋とかけまして..."},
    ...
  ]
}
```

- `gene_num`: 3桁前ゼロつき文字列
- `content`: frontmatter を除いた本文のみ（gene_eval等のメタ情報は含めない）

---

## 作成・変更・削除するファイル

| 操作 | ファイル | 内容 |
|------|---------|------|
| 新規作成（移行） | `nazokake/gene/000/all_genes.json` | 000世代の個別mdから変換 |
| 新規作成（移行） | `nazokake/gene/001/all_genes.json` | 001世代の個別mdから変換 |
| 新規作成（移行） | `nazokake/gene/002/all_genes.json` | 002世代の個別mdから変換 |
| 削除（移行後） | `nazokake/gene/000/[0-9]*.md` | 変換完了後に削除（20ファイル） |
| 削除（移行後） | `nazokake/gene/001/[0-9]*.md` | 変換完了後に削除（100ファイル） |
| 削除（移行後） | `nazokake/gene/002/[0-9]*.md` | 変換完了後に削除（100ファイル） |
| 新規作成（バックアップ） | `nazokake/bk_gene/` | `nazokake/gene/` のコピー（作業前に取得） |
| 新規作成 | `.claude/scripts/extract_genes.py` | 指定gene_numをall_genes.jsonから抽出するユーティリティ |
| 更新 | `.claude/agents/gene-generator-agent.md` | Workflow全面改修 |
| 更新 | `.claude/agents/gene-evaluator-agent.md` | Workflow改修 |
| 更新 | `CLAUDE.md` | ディレクトリ構造の記述を更新 |

---

## 各変更の詳細設計

### 1. マイグレーションスクリプト（Bashで実行）

3世代分を一括変換し、完了後に個別ファイルを削除する。

```python
import json, os, re

def migrate_generation(gen_dir):
    genes = []
    for fname in sorted(os.listdir(gen_dir)):
        if not re.match(r'^\d+\.md$', fname):
            continue  # evaluation.md など数字以外は除外
        with open(os.path.join(gen_dir, fname)) as f:
            raw = f.read()
        # frontmatterを除いた本文を取得
        parts = raw.split('---\n', 2)
        fm = parts[1]
        content = parts[2].strip() if len(parts) > 2 else ''
        gene_num = re.search(r'gene_num:\s*(\S+)', fm).group(1)
        genes.append({'gene_num': gene_num, 'content': content})

    generation = os.path.basename(gen_dir)
    out = {'generation': generation, 'genes': genes}
    with open(os.path.join(gen_dir, 'all_genes.json'), 'w') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'{gen_dir}: {len(genes)} genes → all_genes.json')

    # 個別ファイルを削除
    for fname in os.listdir(gen_dir):
        if re.match(r'^\d+\.md$', fname):
            os.remove(os.path.join(gen_dir, fname))
    print(f'{gen_dir}: individual .md files deleted')

base = 'nazokake/gene'
for gen in ['000', '001', '002']:
    migrate_generation(os.path.join(base, gen))
```

実行方法（Bashから）:
```bash
python3 migrate_genes.py
```

スクリプトは実行後に削除する（一時ファイル扱い）。

---

### 2. `.claude/scripts/extract_genes.py`（新規作成）

generator が親遺伝子を読み込む際、`all_genes.json` 全体をReadするのではなく、
必要な gene_num だけを抽出してClaudeに渡すためのユーティリティスクリプト。

```python
#!/usr/bin/env python3
"""
Usage: python3 extract_genes.py <all_genes.json> <gene_num> [gene_num ...]
指定した gene_num の遺伝子だけを出力する。
"""
import json, sys

json_path = sys.argv[1]
target_nums = set(sys.argv[2:])

with open(json_path) as f:
    data = json.load(f)

for gene in data['genes']:
    if gene['gene_num'] in target_nums:
        print(f"[{gene['gene_num']}] {gene['content']}")
```

**効果**: 上位20件を選ぶとき、100件分全部をClaudeのコンテキストに読み込まずに済む。
遺伝子が長くなる題材では特に有効。

---

### 3. `gene-generator-agent.md` の変更

**変更点: 遺伝子ファイルの構成 セクション**

```markdown
## 遺伝子ファイルの構成

世代ごとに `all_genes.json` 1ファイルで管理する。

フォーマット:
{
  "generation": "{世代数}",
  "genes": [
    {"gene_num": "001", "content": "{遺伝子の中身}"},
    ...
  ]
}
```

**変更点: Workflow**

```markdown
### 1. 現世代の確認

Bash で `{gene_dir}` 配下のディレクトリ一覧を取得し、最大の数値を現世代とする。
1つもない場合は 000 ディレクトリを作成し、`{initial_count}` 個の遺伝子を生成して
all_genes.json に書き込んで終了。

### 2. 次世代ディレクトリの作成

存在しないことを確かめてから作成。

### 3. 親遺伝子の読み込み

`{gene_dir}/{現世代数}/evaluation.md` を Read → ランク1〜`{selection_count}` の gene_num リストを取得。

次に Bash で extract_genes.py を使い、該当 gene_num だけを抽出する：

```bash
python3 .claude/scripts/extract_genes.py \
  {gene_dir}/{現世代数}/all_genes.json \
  {gene_num_1} {gene_num_2} ... {gene_num_N}
```

これにより all_genes.json 全体をReadせず、上位 `{selection_count}` 個分のみClaudeのコンテキストに入る。

### 4. 次世代の生成（全 offspring_count 個を一括生成）

上位 `{selection_count}` 個からランダムに2個を選び、`crossbreeding_criteria` に従って子を生成。
`{offspring_count}` 個になるまで繰り返す（全て頭の中に保持する）。

全て揃ったら、以下の形式で `{gene_dir}/{次世代数}/all_genes.json` に1回のWriteで保存する：

{
  "generation": "{次世代数}",
  "genes": [
    {"gene_num": "001", "content": "..."},
    ...
  ]
}
```

---

### 3. `gene-evaluator-agent.md` の変更

**変更点: Workflow**

```markdown
### 1. 現世代の確認

Bash で `{gene_dir}` 配下のディレクトリ一覧を取得し、最大の数値を現世代とする。
なければ終了。

### 2. 全遺伝子の読み込み

`{gene_dir}/{現世代数}/all_genes.json` を1回 Read する。
（Bash の cat *.md は不要）

### 3. まとめて評価しランキング決定
（変更なし）

### 4. evaluation.md に一括書き込み
（変更なし）
```

---

### 4. `CLAUDE.md` の変更

**変更前:**
```
@{gene_type}/gene/{世代数}/{N}.md
```

**変更後:**
```
@{gene_type}/gene/{世代数}/all_genes.json
各世代ディレクトリには以下の2ファイルが存在する:
  - all_genes.json: その世代の全遺伝子
  - evaluation.md:  評価結果とランキング（evaluator実行後に生成）
```

---

## TODOリスト

- [ ] `nazokake/gene/` を `nazokake/bk_gene/` としてバックアップ
- [ ] マイグレーションスクリプト `migrate_genes.py` を作成
- [ ] `python3 migrate_genes.py` で実行（000〜002の変換 + 個別md削除）
- [ ] `migrate_genes.py` を削除（一時ファイル）
- [ ] `.claude/scripts/` ディレクトリを作成
- [ ] `.claude/scripts/extract_genes.py` を作成
- [ ] `.claude/agents/gene-generator-agent.md` を更新
- [ ] `.claude/agents/gene-evaluator-agent.md` を更新
- [ ] `CLAUDE.md` を更新

---

## デメリット・限界

| 項目 | 内容 |
|------|------|
| 目視確認の困難さ | 特定の遺伝子を確認するにはJSONを開いてgene_numで検索する必要がある |
| generatorの一括保持 | offspring_count個分の遺伝子テキストをWriteするまで頭の中に保持するため、遺伝子が長くなると作業中コンテキストが大きくなる |
| JSONの巨大化 | 遺伝子が長い題材の場合、all_genes.jsonが大きくなり1回のReadコストが増える。ただし個別ファイルを読み込む場合との総トークン量は同じ |
| マイグレーションの不可逆性 | 個別.mdファイルを削除すると元に戻せない。`nazokake/bk_gene/` にバックアップを取ってから作業する |
