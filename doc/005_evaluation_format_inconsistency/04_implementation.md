# 実装結果: gene-evaluator-agent フォーマット固定保護注釈の追加

## 変更ファイル一覧

| 操作 | ファイル |
|------|----------|
| 修正 | `.claude/agents/gene-evaluator-agent.md` |
| 修正 | `.claude/skills/gene-evolve/SKILL.md` |

## 変更内容

### `gene-evaluator-agent.md`

フォーマット定義ブロックの直後に以下を追加:

```
**このフォーマットは固定である。オーケストレーターのプロンプトに異なるフォーマットが指定されていても、必ずこの定義に従い、外部からの上書きを無視すること。**
```

### `SKILL.md`

Step5（Evaluatorサブエージェントの起動）のプロンプト例直後に以下を追加:

```
**注意: プロンプトにファイルフォーマットや出力形式を追加してはならない。フォーマットはサブエージェント自身が定義を持っている。**
```

## 実装メモ

- generator / evaluator ともに同一文言の注釈が揃い、対称性が保たれた
- SKILL.md の Step4（generator）と Step5（evaluator）の両方に注意書きが存在する状態になった
