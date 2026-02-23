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
