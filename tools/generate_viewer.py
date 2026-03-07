"""
遺伝子家系図ビジュアライザー生成スクリプト。
各 gene_type ディレクトリに family_tree.html を出力する。

Usage:
    python tools/generate_viewer.py              # 全 gene_type を処理
    python tools/generate_viewer.py novel140_2   # 指定した gene_type のみ
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

GENERATION_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac",
]

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>家系図: __GENE_TYPE__</title>
<script src="../tools/vendor/cytoscape.min.js"></script>
<script src="../tools/vendor/dagre.min.js"></script>
<script src="../tools/vendor/cytoscape-dagre.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: sans-serif; display: flex; flex-direction: column; height: 100vh; background: #1a1a2e; color: #eee; }
header {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 16px; background: #16213e; border-bottom: 1px solid #0f3460;
  flex-shrink: 0;
}
header h1 { font-size: 16px; color: #e2e8f0; margin-right: auto; }
label { font-size: 13px; color: #a0aec0; }
select, button {
  padding: 4px 10px; border-radius: 4px; border: 1px solid #0f3460;
  background: #0f3460; color: #e2e8f0; font-size: 13px; cursor: pointer;
}
select:hover, button:hover { background: #1a4a8a; }
.main { display: flex; flex: 1; overflow: hidden; }
#cy { flex: 1; }
#panel {
  width: 300px; background: #16213e; border-left: 1px solid #0f3460;
  padding: 16px; overflow-y: auto; font-size: 13px; flex-shrink: 0;
}
#panel h2 { font-size: 14px; color: #90cdf4; margin-bottom: 12px; }
.field { margin-bottom: 10px; }
.field-label { color: #a0aec0; font-size: 11px; text-transform: uppercase; margin-bottom: 2px; }
.field-value { color: #e2e8f0; line-height: 1.5; word-break: break-all; }
.empty { color: #4a5568; font-style: italic; }
#legend { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
</style>
</head>
<body>
<header>
  <h1>家系図: __GENE_TYPE__</h1>
  <label>世代フィルタ:</label>
  <select id="genFilter"><option value="all">全て</option></select>
  <button id="btnReset">表示リセット</button>
  <div id="legend"></div>
</header>
<div class="main">
  <div id="cy"></div>
  <div id="panel">
    <h2>ノード詳細</h2>
    <p class="empty">ノードをクリックしてください</p>
  </div>
</div>
<script>
const GRAPH_DATA = __GRAPH_DATA__;
const COLORS = __COLORS__;

// 世代一覧を収集
const generations = [...new Set(GRAPH_DATA.nodes.map(n => n.data.generation))].sort();

// 世代フィルタ select を構築
const genFilter = document.getElementById('genFilter');
generations.forEach(g => {
  const opt = document.createElement('option');
  opt.value = g;
  opt.textContent = `世代 ${g}`;
  genFilter.appendChild(opt);
});

// 凡例を構築
const legend = document.getElementById('legend');
generations.forEach((g, i) => {
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = `<div class="legend-dot" style="background:${COLORS[i % COLORS.length]}"></div><span>${g}</span>`;
  legend.appendChild(item);
});

// 世代インデックスマップ
const genIndex = {};
generations.forEach((g, i) => { genIndex[g] = i; });

// スタイル生成
function nodeStyle(node) {
  const gen = node.data('generation');
  const color = COLORS[genIndex[gen] % COLORS.length];
  const rank = node.data('rank');
  const size = (rank !== null && rank !== undefined && rank <= 20) ? 28 : 18;
  return { 'background-color': color, 'width': size, 'height': size };
}

// Cytoscape 初期化
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: GRAPH_DATA,
  wheelSensitivity: 0,  // 組み込みのスクロールズームを無効化
  style: [
    {
      selector: 'node',
      style: {
        'width': 18, 'height': 18,
        'label': 'data(gene_num)',
        'font-size': 8,
        'color': '#fff',
        'text-valign': 'center',
        'text-halign': 'center',
        'background-color': ele => COLORS[genIndex[ele.data('generation')] % COLORS.length],
      }
    },
    {
      selector: 'node[rank <= 20]',
      style: { 'width': 28, 'height': 28, 'font-size': 10 }
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 3,
        'border-color': '#ffd700',
      }
    },
    {
      selector: '.highlighted',
      style: {
        'border-width': 2,
        'border-color': '#90cdf4',
        'opacity': 1,
      }
    },
    {
      selector: '.dimmed',
      style: { 'opacity': 0.15 }
    },
    {
      selector: 'edge',
      style: {
        'width': 1,
        'line-color': '#4a5568',
        'target-arrow-color': '#4a5568',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': 0.7,
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'line-color': '#90cdf4',
        'target-arrow-color': '#90cdf4',
        'width': 2,
        'opacity': 1,
      }
    },
  ],
  layout: {
    name: 'dagre',
    rankDir: 'TB',
    nodeSep: 8,
    rankSep: 1100,
    animate: false,
  }
});

// ノードクリック: 詳細表示 + 祖先・子孫ハイライト
cy.on('tap', 'node', function(evt) {
  const node = evt.target;
  const data = node.data();

  // ハイライトリセット
  cy.elements().removeClass('highlighted dimmed');

  // 祖先・子孫を収集
  const ancestors = node.predecessors();
  const descendants = node.successors();
  const related = ancestors.union(descendants).union(node);
  cy.elements().not(related).addClass('dimmed');
  related.addClass('highlighted');
  node.removeClass('dimmed');

  // サイドパネル更新
  const panel = document.getElementById('panel');
  const symbols = (data.symbols || []).join('、') || '—';
  const parents = (data.parents || []).join(', ') || '—（初期個体）';
  const rankText = (data.rank !== null && data.rank !== undefined) ? `${data.rank} 位` : '—';

  panel.innerHTML = `
    <h2>ノード詳細</h2>
    <div class="field">
      <div class="field-label">世代 / gene_num</div>
      <div class="field-value">世代 ${data.generation} / #${data.gene_num}</div>
    </div>
    <div class="field">
      <div class="field-label">ランク</div>
      <div class="field-value">${rankText}</div>
    </div>
    <div class="field">
      <div class="field-label">親 (前世代)</div>
      <div class="field-value">${parents}</div>
    </div>
    <div class="field">
      <div class="field-label">シンボル</div>
      <div class="field-value">${symbols}</div>
    </div>
    <div class="field">
      <div class="field-label">内容</div>
      <div class="field-value">${data.content}</div>
    </div>
  `;
});

// 背景クリック: リセット
cy.on('tap', function(evt) {
  if (evt.target === cy) {
    cy.elements().removeClass('highlighted dimmed');
    document.getElementById('panel').innerHTML = '<h2>ノード詳細</h2><p class="empty">ノードをクリックしてください</p>';
  }
});

// 世代フィルタ
genFilter.addEventListener('change', function() {
  const val = this.value;
  cy.elements().removeClass('highlighted dimmed');
  if (val === 'all') {
    cy.elements().style('display', 'element');
  } else {
    cy.nodes().forEach(n => {
      n.style('display', n.data('generation') === val ? 'element' : 'none');
    });
    cy.edges().forEach(e => {
      const src = e.source().data('generation') === val;
      const tgt = e.target().data('generation') === val;
      e.style('display', (src && tgt) ? 'element' : 'none');
    });
  }
});

// スクロール操作を乗っ取る:
//   通常スクロール → パン（移動）
//   Ctrl/Cmd + スクロール or ピンチ → ズーム
document.getElementById('cy').addEventListener('wheel', function(e) {
  e.preventDefault();
  e.stopPropagation();
  if (e.ctrlKey || e.metaKey) {
    // ズーム（ピンチも ctrlKey=true で来る）
    const factor = e.deltaY > 0 ? 0.85 : 1.18;
    cy.zoom({
      level: cy.zoom() * factor,
      renderedPosition: { x: e.offsetX, y: e.offsetY }
    });
  } else {
    // パン
    cy.panBy({ x: -e.deltaX * 1.5, y: -e.deltaY * 1.5 });
  }
}, { passive: false, capture: true });

// 表示リセット
document.getElementById('btnReset').addEventListener('click', function() {
  genFilter.value = 'all';
  cy.elements().style('display', 'element');
  cy.elements().removeClass('highlighted dimmed');
  cy.fit();
});
</script>
</body>
</html>
"""


def detect_gene_types():
    """criteria.md + gene/ の両方が存在するディレクトリを gene_type として検出する。"""
    gene_types = []
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and (d / "criteria.md").exists() and (d / "gene").is_dir():
            gene_types.append(d.name)
    return gene_types


def parse_evaluation_md(path: Path) -> dict:
    """evaluation.md から {gene_num: rank} の辞書を返す。ファイルがなければ空辞書。"""
    if not path.exists():
        return {}
    ranks = {}
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("| rank"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and re.match(r"^\d+$", parts[0]):
                ranks[parts[1]] = int(parts[0])
    return ranks


def build_graph_data(gene_type: str) -> dict:
    """gene_type の全世代を読み込み Cytoscape.js 用ノード・エッジを構築する。"""
    gene_dir = ROOT / gene_type / "gene"
    generations = sorted(d.name for d in gene_dir.iterdir() if d.is_dir())

    nodes = []
    edges = []

    for gen in generations:
        json_path = gene_dir / gen / "all_genes.json"
        if not json_path.exists():
            continue
        eval_path = gene_dir / gen / "evaluation.md"
        ranks = parse_evaluation_md(eval_path)

        data = json.loads(json_path.read_text(encoding="utf-8"))
        prev_gen = generations[generations.index(gen) - 1] if generations.index(gen) > 0 else None

        for gene in data["genes"]:
            gene_num = gene["gene_num"]
            node_id = f"{gen}__{gene_num}"
            symbols = gene.get("meta", {}).get("symbols", []) if gene.get("meta") else []
            rank = ranks.get(gene_num)

            nodes.append({
                "data": {
                    "id": node_id,
                    "generation": gen,
                    "gene_num": gene_num,
                    "content": gene["content"],
                    "parents": gene.get("parents") or [],
                    "symbols": symbols,
                    "rank": rank,
                }
            })

            for parent_num in (gene.get("parents") or []):
                if prev_gen:
                    edges.append({
                        "data": {
                            "source": f"{prev_gen}__{parent_num}",
                            "target": node_id,
                        }
                    })

    return {"nodes": nodes, "edges": edges}


def generate(gene_type: str):
    print(f"  generating: {gene_type} ...", end="", flush=True)
    graph_data = build_graph_data(gene_type)
    node_count = len(graph_data["nodes"])
    edge_count = len(graph_data["edges"])

    html = HTML_TEMPLATE
    html = html.replace("__GENE_TYPE__", gene_type)
    html = html.replace("__GRAPH_DATA__", json.dumps(graph_data, ensure_ascii=False))
    html = html.replace("__COLORS__", json.dumps(GENERATION_COLORS))

    out_path = ROOT / gene_type / "family_tree.html"
    out_path.write_text(html, encoding="utf-8")
    print(f" done ({node_count} nodes, {edge_count} edges) → {out_path}")


def main():
    args = sys.argv[1:]
    if args:
        gene_types = args
    else:
        gene_types = detect_gene_types()
        print(f"detected gene_types: {gene_types}")

    for gt in gene_types:
        gt_dir = ROOT / gt
        if not gt_dir.is_dir():
            print(f"  error: directory not found: {gt}")
            continue
        generate(gt)

    print("\nDone. Open family_tree.html in each gene_type directory.")


if __name__ == "__main__":
    main()
