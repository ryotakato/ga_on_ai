"""
初回セットアップ用: Cytoscape.js 関連ライブラリを tools/vendor/ にダウンロードする。
一度だけ実行すればよい。

Usage:
    python tools/download_libs.py
"""

import urllib.request
from pathlib import Path

LIBS = {
    "cytoscape.min.js": "https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js",
    "dagre.min.js": "https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js",
    "cytoscape-dagre.min.js": "https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js",
}

def main():
    vendor_dir = Path(__file__).parent / "vendor"
    vendor_dir.mkdir(exist_ok=True)

    for filename, url in LIBS.items():
        dest = vendor_dir / filename
        if dest.exists():
            print(f"  skip (already exists): {filename}")
            continue
        print(f"  downloading: {filename} ...")
        urllib.request.urlretrieve(url, dest)
        print(f"  done: {dest}")

    print("\nAll libraries ready in tools/vendor/")

if __name__ == "__main__":
    main()
