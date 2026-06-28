import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

def main():
    # 1. Detect
    from graphify.detect import detect, save_manifest
    INPUT_PATH = Path('.').resolve()
    Path('graphify-out').mkdir(exist_ok=True)
    detect_res = detect(INPUT_PATH)
    Path('graphify-out/.graphify_detect.json').write_text(json.dumps(detect_res, ensure_ascii=False), encoding='utf-8')

    # 2. Extract AST
    from graphify.extract import collect_files, extract
    code_files = []
    for f in detect_res.get('files', {}).get('code', []):
        p = Path(f)
        code_files.extend(collect_files(p) if p.is_dir() else [p])

    ast_result = {'nodes': [], 'edges': [], 'input_tokens': 0, 'output_tokens': 0}
    if code_files:
        ast_result = extract(code_files, cache_root=INPUT_PATH)

    Path('graphify-out/.graphify_extract.json').write_text(json.dumps(ast_result, ensure_ascii=False), encoding='utf-8')
    print(f"Extraction: {len(ast_result['nodes'])} nodes, {len(ast_result['edges'])} edges")

    # 3. Build & Cluster
    from graphify.build import build_from_json
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_json

    G = build_from_json(ast_result, root=str(INPUT_PATH), directed=True)
    if G.number_of_nodes() == 0:
        print("ERROR: Graph is empty.")
        sys.exit(1)

    communities = cluster(G)
    cohesion = score_all(G, communities)
    tokens = {'input': 0, 'output': 0}
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    labels = {cid: f'Community {cid}' for cid in communities}
    questions = suggest_questions(G, communities, labels)

    # Write graph.json
    wrote = to_json(G, communities, 'graphify-out/graph.json', force=True)
    if not wrote:
        print("ERROR: graph.json was not written. Use force.")

    # Write report
    report = generate(G, communities, cohesion, labels, gods, surprises, detect_res, tokens, str(INPUT_PATH), suggested_questions=questions)
    Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')

    analysis = {
        'communities': {str(k): v for k, v in communities.items()},
        'cohesion': {str(k): v for k, v in cohesion.items()},
        'gods': gods,
        'surprises': surprises,
        'questions': questions,
    }
    Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding='utf-8')

    # 4. Generate HTML and other outputs
    os.system('graphify export html')

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities")

if __name__ == '__main__':
    main()
