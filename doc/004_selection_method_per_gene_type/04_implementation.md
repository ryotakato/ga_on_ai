# 実装結果: 選択手法スクリプト化と meta フィールド対応

## 変更・作成ファイル一覧

| 操作 | ファイル |
|------|----------|
| 新規作成 | `.claude/scripts/select_parents.py` |
| 修正 | `.claude/agents/gene-generator-agent.md` |
| 修正 | `.claude/skills/gene-evolve/SKILL.md` |
| 新規作成 | `novel140_2/criteria.md` |
| 新規作成 | `novel140_2/gene/.gitkeep` |

## 実装メモ

### `select_parents.py`

- 4手法を1スクリプトに統合。`--method` で切り替え。
- `parse_evaluation()` は `| rank | gene_num |` のMarkdown表形式をパース。rank列の整数でソートしてランク順リストを返す。
- `elite_plus_random` の「残り」は `ranked[selection_count:]`（評価済み遺伝子の下位群）を使用。`all_nums` は受け取るが使用しない（将来の拡張用に引数定義は残した）。
- `rank_proportionate` の重みは線形ランク重み（1位=n、最下位=1）。スコア差は反映せずランク順位のみ考慮。
- `tournament` は独立した2回のトーナメントで親A・親Bをそれぞれ選出（同じ遺伝子が両親になる可能性あり）。

### `gene-generator-agent.md`

- 入力パラメータに `selection_method`, `diversity_count`, `tournament_size`, `meta_fields` を追加。
- Step3 を `select_parents.py` 呼び出しに全面書き換え。evaluation.md の直接Readは不要になった。
- Step4 の親選択ロジック「ランダムに2個選ぶ」を「スクリプト出力のi行目をそのまま使う」に変更。
- JSON フォーマット定義に `meta` フィールド（オプション）を追加。`meta_fields` が空でない場合のみ付与。

### `SKILL.md`

- Step2（criteria.md 読み込み）に新フィールド4つを追加、省略時デフォルト値も明記。
- Step4（Generator起動プロンプト）に新フィールド4つを追加。

### `novel140_2/`

- `novel140/criteria.md` をベースにコピーし、以下を変更：
  - `gene_type: novel140_2`
  - `selection_method: elite_plus_random`
  - `selection_count: 10`（20 → 10）
  - `diversity_count: 10` 追加
  - `meta_fields: [symbols]` 追加
- `novel140` の既存データは変更なし。

## 後方互換性

- `criteria.md` に `selection_method` が未定義の場合、SKILL.md がデフォルト `elite` を使用する。nazokake など既存の gene_type はそのまま動作する。
