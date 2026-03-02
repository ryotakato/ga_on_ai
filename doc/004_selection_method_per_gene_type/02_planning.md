# 計画: 選択手法スクリプト化と meta フィールド対応

## アプローチ

**中心となるアイデア**: 選択手法ごとのロジックをPythonスクリプトに封じ込め、`gene-generator-agent` はスクリプトを呼ぶだけにする。サブエージェントは「どの手法か」を `criteria.md` から読んでスクリプトに渡すだけでよく、手法の詳細を知る必要がない。

---

## スクリプト設計: `select_parents.py`

4手法を1つのスクリプトに統合する（`--method` で切り替え）。

### インターフェース

```bash
python3 .claude/scripts/select_parents.py \
  <all_genes_path> \
  <evaluation_path> \
  --method {elite|elite_plus_random|rank_proportionate|tournament} \
  --offspring_count N \
  [--selection_count N]   # elite / elite_plus_random 共通
  [--diversity_count M]   # elite_plus_random のみ
  [--tournament_size K]   # tournament のみ
```

### 出力形式

`offspring_count` 行、各行に空白区切りの親ペア（gene_num × 2）を出力する。

```
003 047
021 089
056 012
...（offspring_count 行）
```

**ポイント**: スクリプトが乱数サンプリングを担当するため、エージェントはランダム選択を行わなくてよい。出力されたペアをそのまま使って子を生成するだけになる。

### 各手法の内部ロジック

| 手法 | ロジック |
|------|----------|
| `elite` | evaluation.md から上位 selection_count 個の gene_num を取得し、そこから offspring_count ペアをランダムサンプリング |
| `elite_plus_random` | 上位 selection_count 個 ＋ 残りからランダム diversity_count 個を親プールとし、offspring_count ペアをサンプリング |
| `rank_proportionate` | 線形ランク重みで全遺伝子に確率を割り当て、重み付きサンプリングで offspring_count ペアを生成 |
| `tournament` | offspring_count 回トーナメントを実施（毎回 tournament_size 個をランダム抽出し最高ランクを選出）して親ペアを生成 |

---

## criteria.md への追加フィールド

```yaml
---
gene_type: novel140
initial_count: 100
selection_method: elite_plus_random   # 追加（未定義時は elite で後方互換）
selection_count: 10                   # エリート枠（既存。意味を変更）
diversity_count: 10                   # 追加（elite_plus_random のみ）
tournament_size: 5                    # 追加（tournament のみ）
offspring_count: 100
meta_fields:                          # 追加（オプション）
  - symbols
---
```

---

## 変更・作成ファイル一覧

| 操作 | ファイル | 内容 |
|------|----------|------|
| **新規作成** | `.claude/scripts/select_parents.py` | 4手法統合の親選択スクリプト |
| **修正** | `.claude/agents/gene-generator-agent.md` | ワークフロー Step3〜4 の書き換え、meta 対応 |
| **修正** | `.claude/skills/gene-evolve/SKILL.md` | Step2〜4 の新フィールド対応 |
| **新規作成** | `novel140_2/criteria.md` | `novel140/criteria.md` をベースに新フィールドを追加（elite_plus_random 設定）|
| **新規作成** | `novel140_2/gene/` | 遺伝子ディレクトリ（空で作成）|

nazokake の `criteria.md` は現状 `selection_method` 未定義のままにする（後方互換で `elite` 動作）。
`novel140` の既存ディレクトリは変更しない。新設計は `novel140_2` で独立して試す。

---

## 各ファイルの変更内容

### `gene-generator-agent.md` の変更

**入力パラメータに追加:**

```
- `selection_method`: 選択手法（省略時: elite）
- `diversity_count`: ランダム枠数（elite_plus_random の場合）
- `tournament_size`: トーナメントサイズ（tournament の場合）
- `meta_fields`: 記録するメタフィールドのリスト（省略可）
```

**Step3 の書き換え（現行の手動エリート選択をスクリプト化）:**

```bash
# 現行
# evaluation.md を Read して上位N個の gene_num を取得し extract_genes.py を呼ぶ

# 新規
python3 .claude/scripts/select_parents.py \
  {gene_dir}/{現世代数}/all_genes.json \
  {gene_dir}/{現世代数}/evaluation.md \
  --method {selection_method} \
  --offspring_count {offspring_count} \
  [--selection_count {selection_count}] \
  [--diversity_count {diversity_count}] \
  [--tournament_size {tournament_size}]
```

出力の各行が1子に対応する親ペア。ユニークな gene_num を collect し、`extract_genes.py` で内容を取得する。

**Step4 の変更:**

「上位N個からランダムに2個選ぶ」→「select_parents.py の出力行の順に親ペアを使う（i 行目 = 子i の親ペア）」

**JSONフォーマットの変更（meta 対応）:**

```json
{
  "gene_num": "001",
  "content": "小説本文...",
  "parents": ["050", "023"],
  "meta": {
    "symbols": ["ねこさがしています", "初めて手をつないだ・理由は同じ"]
  }
}
```

`meta_fields` が定義されている場合のみ `meta` キーを追加。`meta.symbols` はジェネレーターが掛け合わせに使った象徴を記録する。

### `SKILL.md` の変更

Step2（criteria.md 読み込み）に取得フィールドを追加：

```
- selection_method（省略時: elite）
- diversity_count（省略時: 0）
- tournament_size（省略時: 3）
- meta_fields（省略時: 空リスト）
```

Step4（Generator起動プロンプト）に追加：

```
selection_method: {selection_method}
diversity_count: {diversity_count}
tournament_size: {tournament_size}
meta_fields: {meta_fields}
```

---

## デメリット・限界

- `select_parents.py` が evaluation.md のフォーマット（現行の `| rank | gene_num |` 表形式）に依存する。evaluator の出力形式が変わると壊れる。
- `rank_proportionate` は線形ランク重みを使用するため、スコア差の大きさは選択確率に反映されない（ランク順位のみ考慮）。
- `meta_fields` 対応はジェネレーターの指示に依存するため、フィールド名の解釈はLLMに委ねられる（構造化された検証はない）。

---

## TODO リスト

1. `.claude/scripts/select_parents.py` を作成する
2. `.claude/agents/gene-generator-agent.md` を修正する
   - 入力パラメータに `selection_method`, `diversity_count`, `tournament_size`, `meta_fields` を追加
   - Step3: `select_parents.py` 呼び出しに書き換え
   - Step4: 親ペアの使い方を「出力行順に使う」に変更
   - JSONフォーマットに optional `meta` フィールドを追加
3. `.claude/skills/gene-evolve/SKILL.md` を修正する
   - Step2: 新フィールドを読み込む
   - Step4: Generator プロンプトに新フィールドを渡す
4. `novel140_2/` ディレクトリを新規作成する
   - `novel140_2/criteria.md`: `novel140/criteria.md` をベースにコピーし、以下を追加・変更
     - `gene_type: novel140_2`
     - `selection_method: elite_plus_random`
     - `selection_count: 10`（20 → 10）
     - `diversity_count: 10` を追加
     - `meta_fields: [symbols]` を追加
   - `novel140_2/gene/` ディレクトリを作成（空）
