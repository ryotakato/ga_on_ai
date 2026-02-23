# GA on AI — AIと遺伝的アルゴリズムによるコンテンツ生成

Claude Code（AI）を使い、遺伝的アルゴリズムの枠組みでコンテンツを世代を重ねながら進化させる実験的プロジェクト。

生成・評価・選択・交叉を繰り返すことで、定義した評価基準に沿ったコンテンツが世代ごとに洗練されていく。

## 概要

- 遺伝子（Gene）: 生成対象のコンテンツ単位（例: なぞかけ）
- 世代（Generation）: 生成・評価サイクルの1ループ
- criteria.md: 交叉ルールと評価基準を定義するファイル
- Claude Code スキル: `gene-evolve` スキルがオーケストレーターとして動作し、生成・評価のサブエージェントを制御する


## 使い方

Claude Code のスキル `gene-evolve` を呼び出す。

```
# フルサイクル（生成 → 評価）
nazokake を進化させて

# 生成のみ
nazokake を生成だけして

# 評価のみ
nazokake を評価だけして
```

内部では以下が自動実行される：

1. `criteria.md` を読み込み、パラメータ・交叉ルール・評価基準を取得
2. Generator サブエージェントが前世代の上位個体を親として次世代を生成
3. Evaluator サブエージェントが生成された個体を評価・ランキング

## 新しい遺伝子タイプの追加

1. `{gene_type}/` ディレクトリを作成する
2. `{gene_type}/criteria.md` を以下の形式で記述する

```markdown
---
gene_type: {gene_type}
initial_count: 20      # 初期世代の個体数
selection_count: 20    # 次世代へ引き継ぐ上位個体数
offspring_count: 100   # 次世代で生成する子個体数
---

## crossbreeding
（交叉ルールを記述）

## evaluation
（評価基準を記述）
```

3. `{gene_type}/gene/000/all_genes.json` に初期遺伝子を作成する (作成しない場合はClaude Codeに任せることになる)
4. Claude Code で `{gene_type} を進化させて` と指示する



## ディレクトリ構造

```
{gene_type}/
  criteria.md                    ← 交叉ルール・評価基準・パラメータ
  gene/
    {世代数（例: 001）}/
      all_genes.json             ← その世代の全遺伝子（1ファイルに一括管理）
      evaluation.md              ← 評価結果とランキング

.claude/
  skills/
    gene-evolve/
      SKILL.md                   ← オーケストレータースキルの定義
  agents/
    gene-generator-agent.md      ← 生成サブエージェントの定義
    gene-evaluator-agent.md      ← 評価サブエージェントの定義
  scripts/
    extract_genes.py             ← ユーティリティスクリプト

doc/                             ← 開発ドキュメント（開発者向け）
```

## doc ディレクトリについて

`doc/` 配下はこのプロジェクトの開発過程のドキュメント。設計の調査・計画・実装メモが格納されているため、エンドユーザーは特に確認する必要なし。


