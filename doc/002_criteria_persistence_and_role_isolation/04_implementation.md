# 実装結果: criteria永続化 + サブエージェントによる役割分離

実装日: 2026-02-23

---

## 実施したTODO

- [x] `.claude/agents/` ディレクトリを作成
- [x] `.claude/agents/gene-generator-agent.md` を作成
- [x] `.claude/agents/gene-evaluator-agent.md` を作成
- [x] `.claude/skills/gene-evolve/` ディレクトリを作成
- [x] `.claude/skills/gene-evolve/SKILL.md` を作成
- [x] `nazokake/` ディレクトリを作成
- [x] `nazokake/criteria.md` をプレースホルダーとして作成
- [x] `nazokake/gene/` ディレクトリを作成
- [x] `gene/` 配下の全ファイルを `nazokake/gene/` へ移動
- [x] `gene/` ディレクトリを削除
- [x] `CLAUDE.md` のディレクトリ構造の記述を更新
- [x] `.claude/skills/gene-generator/` を削除
- [x] `.claude/skills/gene-evaluator/` を削除

---

## 変更・作成・削除ファイル一覧

### 新規作成

| ファイル | 内容 |
|---------|------|
| `.claude/agents/gene-generator-agent.md` | ジェネレーターサブエージェント定義 |
| `.claude/agents/gene-evaluator-agent.md` | エバリュエーターサブエージェント定義 |
| `.claude/skills/gene-evolve/SKILL.md` | オーケストレータースキル（full/generate-only/evaluate-onlyモード対応） |
| `nazokake/criteria.md` | なぞかけ用criteriaプレースホルダー（中身はユーザーが記入） |

### 移動

| 操作 | 内容 |
|------|------|
| `gene/000/` → `nazokake/gene/000/` | 遺伝子データ（20件） |
| `gene/001/` → `nazokake/gene/001/` | 遺伝子データ（100件）+ evaluation.md |
| `gene/002/` → `nazokake/gene/002/` | 遺伝子データ（100件）+ evaluation.md |

### 更新

| ファイル | 変更内容 |
|---------|---------|
| `CLAUDE.md` | ディレクトリ構造を `{gene_type}/gene/{世代数}/{N}.md` に更新。criteria.mdの説明を追加。 |

### 削除

| ファイル | 理由 |
|---------|------|
| `gene/`（ディレクトリ） | 中身を nazokake/gene/ へ移動後、空になったため削除 |
| `.claude/skills/gene-generator/`（ディレクトリごと） | サブエージェント定義に移行のため廃止 |
| `.claude/skills/gene-evaluator/`（ディレクトリごと） | サブエージェント定義に移行のため廃止 |

---

## 実装後のディレクトリ構造

```
generate/
  nazokake/
    criteria.md           ← ★プレースホルダー。crossbreeding/evaluationをtaviが記入すること
    gene/
      000/（20件）
      001/（100件 + evaluation.md）
      002/（100件 + evaluation.md）
  .claude/
    agents/
      gene-generator-agent.md
      gene-evaluator-agent.md
    skills/
      gene-evolve/
        SKILL.md
  CLAUDE.md
  doc/
    ...
```

---

## 実装メモ

### nazokake/criteria.md はプレースホルダー

`crossbreeding` と `evaluation` セクションの中身は空欄のままにした。taviが実際の基準を記入する必要がある。

### gene-evolve の動作モード

| モード | 起動条件 |
|--------|---------|
| `full` | 「進化させて」「GAを回して」 / デフォルト |
| `generate-only` | 「生成だけして」「次世代だけ作って」 |
| `evaluate-only` | 「評価だけして」「今の世代を評価して」 |

### サブエージェントへ渡すパラメータ

**gene-generator-agent に渡すもの:**
- `gene_dir`, `crossbreeding_criteria`, `initial_count`, `selection_count`, `offspring_count`
- evaluationセクションは含めない

**gene-evaluator-agent に渡すもの:**
- `gene_dir`, `evaluation_criteria`
- crossbreedingセクションは含めない
