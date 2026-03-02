#!/usr/bin/env python3
"""
Usage: python3 select_parents.py <all_genes_path> <evaluation_path>
  --method {elite|elite_plus_random|rank_proportionate|tournament}
  --offspring_count N
  [--selection_count N]   # elite / elite_plus_random
  [--diversity_count M]   # elite_plus_random only
  [--tournament_size K]   # tournament only

Output: offspring_count lines, each with 2 space-separated gene_nums (parent pair)
"""
import json, re, random, argparse


def parse_evaluation(eval_path):
    """evaluation.md の | rank | gene_num | テーブルをパースし、ランク順の gene_num リストを返す"""
    ranked = []
    with open(eval_path) as f:
        for line in f:
            m = re.match(r'\|\s*(\d+)\s*\|\s*(\w+)\s*\|', line)
            if m:
                ranked.append((int(m.group(1)), m.group(2)))
    ranked.sort(key=lambda x: x[0])
    return [gene_num for _, gene_num in ranked]


def load_all_gene_nums(genes_path):
    """all_genes.json から全 gene_num を返す"""
    with open(genes_path) as f:
        data = json.load(f)
    return [g['gene_num'] for g in data['genes']]


def sample_pair(pool):
    """pool から2個サンプリング（pool が1個の場合は同じ個体を2回）"""
    if len(pool) < 2:
        return (pool[0], pool[0])
    return tuple(random.sample(pool, 2))


def select_elite(ranked, selection_count, offspring_count, **kwargs):
    pool = ranked[:selection_count]
    return [sample_pair(pool) for _ in range(offspring_count)]


def select_elite_plus_random(ranked, selection_count, diversity_count, offspring_count, **kwargs):
    elite = ranked[:selection_count]
    rest = ranked[selection_count:]
    random_pick = random.sample(rest, min(diversity_count, len(rest)))
    pool = elite + random_pick
    return [sample_pair(pool) for _ in range(offspring_count)]


def select_rank_proportionate(ranked, offspring_count, **kwargs):
    n = len(ranked)
    # 線形ランク重み: 1位=n, 最下位=1
    weights = list(range(n, 0, -1))
    pairs = []
    for _ in range(offspring_count):
        a, b = random.choices(ranked, weights=weights, k=2)
        pairs.append((a, b))
    return pairs


def select_tournament(ranked, tournament_size, offspring_count, **kwargs):
    rank_map = {gene_num: i for i, gene_num in enumerate(ranked)}

    def tournament_winner():
        candidates = random.sample(ranked, min(tournament_size, len(ranked)))
        return min(candidates, key=lambda g: rank_map[g])

    pairs = []
    for _ in range(offspring_count):
        a = tournament_winner()
        b = tournament_winner()
        pairs.append((a, b))
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('all_genes_path')
    parser.add_argument('evaluation_path')
    parser.add_argument('--method', required=True,
                        choices=['elite', 'elite_plus_random', 'rank_proportionate', 'tournament'])
    parser.add_argument('--offspring_count', type=int, required=True)
    parser.add_argument('--selection_count', type=int, default=10)
    parser.add_argument('--diversity_count', type=int, default=10)
    parser.add_argument('--tournament_size', type=int, default=3)
    args = parser.parse_args()

    ranked = parse_evaluation(args.evaluation_path)
    all_nums = load_all_gene_nums(args.all_genes_path)

    methods = {
        'elite': select_elite,
        'elite_plus_random': select_elite_plus_random,
        'rank_proportionate': select_rank_proportionate,
        'tournament': select_tournament,
    }

    pairs = methods[args.method](
        ranked=ranked,
        all_nums=all_nums,
        selection_count=args.selection_count,
        diversity_count=args.diversity_count,
        tournament_size=args.tournament_size,
        offspring_count=args.offspring_count,
    )

    for a, b in pairs:
        print(f"{a} {b}")


if __name__ == '__main__':
    main()
