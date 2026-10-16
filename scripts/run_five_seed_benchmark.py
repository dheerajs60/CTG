"""
Five-Seed Temporal Link Prediction Benchmark for APEX-IDS2026 and CIC-IDS2017.
Evaluates:
- Persistence
- EdgeBank-∞ (binary & frequency)
- EdgeBank-tw (W=2, binary & frequency)
- Common Neighbors (directed)
- Jaccard Coefficient (undirected)
- Adamic-Adar (undirected)
- EvolveGCN-H (trained on train partition with topological node features)

Under two strictly separated evaluation settings:
- Setting A: Hard Historical Negatives (edges previously observed but inactive at t+1)
- Setting B: Mixed Random Negatives (uniform non-edges without replacement)

Computes Mean ± Std and 95% Confidence Intervals across 5 seeds: [42, 100, 123, 456, 999].
Saves structured CSV and JSON outputs in results/metrics/.
"""

import sys
import time
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb
import torch
import torch.nn as nn
import torch.optim as optim

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models.baselines import (
    PersistenceBaseline,
    EdgeBankUnlimited,
    EdgeBankTimeWindow,
    CommonNeighborsBaseline,
    JaccardBaseline,
    AdamicAdarBaseline
)
from models.evolve_gcn import EvolveGCNH, compute_topological_node_features
from src.evaluation.candidate_sampler import (
    stratify_edges,
    sample_hard_historical_negatives,
    sample_mixed_negatives,
    create_evaluation_dataset
)
from src.evaluation.metrics import (
    compute_classification_metrics,
    compute_ranking_metrics
)

METRICS_DIR = REPO_ROOT / "results/metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)
RAW_RESULTS_FILE = METRICS_DIR / "benchmark_five_seed_results.json"
SUMMARY_CSV_FILE = METRICS_DIR / "benchmark_five_seed_summary.csv"

SEEDS = [42, 100, 123, 456, 999]


def load_cic_snapshots():
    """Loads 5 daily snapshots from CIC-IDS2017 via DuckDB."""
    cic_csv_glob = str(REPO_ROOT / "datasets/cic_ids2017/TrafficLabelling /*.csv")
    con = duckdb.connect()
    ts_expr = """
        COALESCE(
            try_strptime(Timestamp, '%d/%m/%Y %H:%M:%S'),
            try_strptime(Timestamp, '%d/%m/%Y %H:%M'),
            try_strptime(Timestamp, '%m/%d/%Y %H:%M:%S'),
            try_strptime(Timestamp, '%m/%d/%Y %H:%M')
        )
    """
    query = f"""
        SELECT 
            date_trunc('day', {ts_expr}) as window_start,
            \"Source IP\" as src_ip,
            \"Destination IP\" as dst_ip,
            COUNT(*) as flow_count
        FROM read_csv('{cic_csv_glob}', header=True, ignore_errors=True)
        WHERE Timestamp IS NOT NULL AND \"Source IP\" IS NOT NULL AND \"Destination IP\" IS NOT NULL
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
    """
    df_edges = con.execute(query).df().dropna(subset=['window_start'])
    snapshots = []
    days = sorted(df_edges['window_start'].unique())
    for d in days:
        sub = df_edges[df_edges['window_start'] == d]
        edges = set(zip(sub['src_ip'], sub['dst_ip']))
        nodes = set(sub['src_ip']).union(set(sub['dst_ip']))
        snapshots.append({
            "window_id": str(d)[:10],
            "edges": edges,
            "nodes": nodes
        })
    return snapshots


def load_apex_snapshots():
    """Loads daily snapshots from APEX-IDS2026 pre-extracted parquet edge lists."""
    edge_lists_dir = REPO_ROOT / "results/apex_ids2026/graphs/edge_lists"
    windows = sorted([d.name for d in edge_lists_dir.iterdir() if d.is_dir()])
    snapshots = []
    for w in windows:
        date_str = w.split('=')[1]
        df = pd.read_parquet(edge_lists_dir / w)
        edges = set(zip(df['src_ip'], df['dst_ip']))
        nodes = set(df['src_ip']).union(set(df['dst_ip']))
        snapshots.append({
            "window_id": date_str,
            "edges": edges,
            "nodes": nodes
        })
    return snapshots


def train_evolvegcn(train_snapshots, node2id, in_dim=16, out_dim=16, epochs=5, lr=0.005, seed=42):
    """Trains EvolveGCN-H on the training partition using topological node features."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    num_nodes = len(node2id)
    model = EvolveGCNH(num_nodes=num_nodes, in_channels=in_dim, out_channels=out_dim)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()
    
    model.train()
    for ep in range(epochs):
        h_state = None
        for t in range(len(train_snapshots) - 1):
            G_t = train_snapshots[t]
            G_next = train_snapshots[t+1]
            
            edge_idx_list = [[node2id[u], node2id[v]] for u, v in sorted(G_t['edges']) if u in node2id and v in node2id]
            edge_idx = torch.tensor(edge_idx_list, dtype=torch.long).T if edge_idx_list else torch.zeros((2, 0), dtype=torch.long)
            
            x_topo = compute_topological_node_features(edge_idx, num_nodes, in_dim)
            emb, h_state = model.forward_graph(x_topo, edge_idx, h_state)
            
            pos_edges = sorted(list(G_next['edges']))[:500]
            if not pos_edges: continue
            
            # Fast training negative sampling
            nodes_curr = sorted(list(G_t['nodes']))
            if len(nodes_curr) < 2: continue
            
            neg_edges = []
            for _ in range(len(pos_edges)):
                u, v = np.random.choice(nodes_curr, size=2, replace=False)
                if (u, v) not in G_next['edges']:
                    neg_edges.append((u, v))
                    
            if not neg_edges: continue
            
            cands = pos_edges[:len(neg_edges)] + neg_edges
            labels = torch.tensor([1.0]*len(neg_edges) + [0.0]*len(neg_edges), dtype=torch.float)
            cands_idx = torch.tensor([[node2id[u], node2id[v]] for u, v in cands], dtype=torch.long).T
            
            optimizer.zero_grad()
            logits = model.predict_edges(emb, cands_idx)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            
            h_state = h_state.detach()
            
    model.eval()
    return model


def evaluate_dataset_benchmark(dataset_name, snapshots, train_end_idx, val_end_idx, seeds=SEEDS, max_cands_per_step=2000):
    print("\n" + "=" * 70)
    print(f"BENCHMARKING: {dataset_name} ({len(snapshots)} snapshots, Train: 0-{train_end_idx}, Val: {train_end_idx+1}-{val_end_idx}, Test: {val_end_idx+1}-{len(snapshots)-1})")
    print("=" * 70)
    
    global_nodes = sorted(list(set().union(*[s["nodes"] for s in snapshots])))
    node2id = {n: i for i, n in enumerate(global_nodes)}
    num_nodes = len(global_nodes)
    in_dim = 16
    out_dim = 16
    
    test_transitions = list(range(val_end_idx, len(snapshots) - 1))
    if not test_transitions:
        test_transitions = list(range(train_end_idx, len(snapshots) - 1))
        
    all_seed_results = []
    
    for s_idx, seed in enumerate(seeds):
        print(f"\n--- Running Seed {seed} ({s_idx+1}/{len(seeds)}) on {dataset_name} ---")
        
        # 1. Train EvolveGCN-H on train split
        train_snaps = snapshots[:train_end_idx + 1]
        model_gcn = train_evolvegcn(train_snaps, node2id, in_dim=in_dim, out_dim=out_dim, epochs=3, seed=seed)
        
        # 2. Advance EvolveGCN-H hidden state through train + val
        h_state_test = None
        with torch.no_grad():
            for t in range(val_end_idx):
                G_t = snapshots[t]
                edge_idx_list = [[node2id[u], node2id[v]] for u, v in sorted(G_t['edges'])]
                edge_idx = torch.tensor(edge_idx_list, dtype=torch.long).T if edge_idx_list else torch.zeros((2, 0), dtype=torch.long)
                x_topo = compute_topological_node_features(edge_idx, num_nodes, in_dim)
                _, h_state_test = model_gcn.forward_graph(x_topo, edge_idx, h_state_test)
                
        # 3. Setup Baselines
        baselines = [
            PersistenceBaseline(),
            EdgeBankUnlimited(mode="binary"),
            EdgeBankUnlimited(mode="frequency"),
            EdgeBankTimeWindow(window_size=2, mode="binary"),
            CommonNeighborsBaseline(directed=True),
            JaccardBaseline(directed=False),
            AdamicAdarBaseline(directed=False)
        ]
        
        # Catch up baselines to val_end_idx
        historical_edges = set()
        historical_nodes = set()
        for t in range(val_end_idx):
            historical_edges.update(snapshots[t]['edges'])
            historical_nodes.update(snapshots[t]['nodes'])
            for b in baselines:
                b.update(snapshots[t]['edges'], timestamp=t)
                
        # Evaluate on test transitions
        seed_record = {
            "dataset": dataset_name,
            "seed": seed,
            "setting_a_hard": {},
            "setting_b_mixed": {}
        }
        
        for t in test_transitions:
            G_curr = snapshots[t]
            G_next = snapshots[t+1]
            
            historical_edges.update(G_curr['edges'])
            historical_nodes.update(G_curr['nodes'])
            
            # Update baselines with G_curr
            for b in baselines:
                b.update(G_curr['edges'], timestamp=t)
                
            # Update GCN with G_curr
            edge_idx_list = [[node2id[u], node2id[v]] for u, v in sorted(G_curr['edges'])]
            edge_idx = torch.tensor(edge_idx_list, dtype=torch.long).T if edge_idx_list else torch.zeros((2, 0), dtype=torch.long)
            x_topo = compute_topological_node_features(edge_idx, num_nodes, in_dim)
            with torch.no_grad():
                emb_gcn, h_state_test = model_gcn.forward_graph(x_topo, edge_idx, h_state_test)
                
            # Stratify target edges
            strat = stratify_edges(G_curr['edges'], G_next['edges'], historical_nodes=historical_nodes)
            eligible_pos = sorted(list(strat["recurring"].union(strat["new_between_known"])))
            if not eligible_pos: continue
            
            pos_sample = eligible_pos[:max_cands_per_step]
            k = len(pos_sample)
            
            # Setting A: Hard Historical Negatives
            inactive_hist = historical_edges - G_next['edges']
            num_hard = min(k, len(inactive_hist))
            if num_hard > 0:
                neg_hard = sample_hard_historical_negatives(
                    historical_edges=historical_edges,
                    target_edges=G_next['edges'],
                    num_negatives=num_hard,
                    seed=seed + t
                )
                cands_a, labels_a = create_evaluation_dataset(pos_sample[:num_hard], neg_hard, seed=seed + 100 + t)
                
                for b in baselines:
                    scores = b.predict_scores(cands_a)
                    preds = b.predict_binary(cands_a, threshold=0.5 if b.name.startswith("EdgeBank") or b.name == "Persistence" else 1.0)
                    cls_m = compute_classification_metrics(labels_a, preds.tolist())
                    rank_m = compute_ranking_metrics(labels_a, scores, is_ranking_eligible=b.is_ranking_eligible)
                    if b.name not in seed_record["setting_a_hard"]:
                        seed_record["setting_a_hard"][b.name] = []
                    seed_record["setting_a_hard"][b.name].append({**cls_m, **rank_m})
                    
                # GCN on Setting A
                cands_idx_a = torch.tensor([[node2id[u], node2id[v]] for u, v in cands_a], dtype=torch.long).T
                with torch.no_grad():
                    probs_a = torch.sigmoid(model_gcn.predict_edges(emb_gcn, cands_idx_a)).numpy()
                    preds_gcn_a = (probs_a >= 0.5).astype(int)
                cls_gcn_a = compute_classification_metrics(labels_a, preds_gcn_a.tolist())
                rank_gcn_a = compute_ranking_metrics(labels_a, probs_a, is_ranking_eligible=True)
                if "EvolveGCN-H" not in seed_record["setting_a_hard"]:
                    seed_record["setting_a_hard"]["EvolveGCN-H"] = []
                seed_record["setting_a_hard"]["EvolveGCN-H"].append({**cls_gcn_a, **rank_gcn_a})
                
            # Setting B: Mixed Random Negatives
            known_nodes_list = sorted(list(G_curr['nodes']))
            if len(known_nodes_list) >= 2:
                neg_mixed = sample_mixed_negatives(
                    known_nodes=known_nodes_list,
                    target_edges=G_next['edges'],
                    num_negatives=k,
                    seed=seed + 200 + t
                )
                cands_b, labels_b = create_evaluation_dataset(pos_sample, neg_mixed, seed=seed + 300 + t)
                
                for b in baselines:
                    scores = b.predict_scores(cands_b)
                    preds = b.predict_binary(cands_b, threshold=0.5 if b.name.startswith("EdgeBank") or b.name == "Persistence" else 1.0)
                    cls_m = compute_classification_metrics(labels_b, preds.tolist())
                    rank_m = compute_ranking_metrics(labels_b, scores, is_ranking_eligible=b.is_ranking_eligible)
                    if b.name not in seed_record["setting_b_mixed"]:
                        seed_record["setting_b_mixed"][b.name] = []
                    seed_record["setting_b_mixed"][b.name].append({**cls_m, **rank_m})
                    
                # GCN on Setting B
                cands_idx_b = torch.tensor([[node2id[u], node2id[v]] for u, v in cands_b], dtype=torch.long).T
                with torch.no_grad():
                    probs_b = torch.sigmoid(model_gcn.predict_edges(emb_gcn, cands_idx_b)).numpy()
                    preds_gcn_b = (probs_b >= 0.5).astype(int)
                cls_gcn_b = compute_classification_metrics(labels_b, preds_gcn_b.tolist())
                rank_gcn_b = compute_ranking_metrics(labels_b, probs_b, is_ranking_eligible=True)
                if "EvolveGCN-H" not in seed_record["setting_b_mixed"]:
                    seed_record["setting_b_mixed"]["EvolveGCN-H"] = []
                seed_record["setting_b_mixed"]["EvolveGCN-H"].append({**cls_gcn_b, **rank_gcn_b})
                
        all_seed_results.append(seed_record)
        print(f"  Finished Seed {seed} across {len(test_transitions)} transitions.")
        
    return all_seed_results


def aggregate_benchmark_results(results_list):
    """
    Computes Mean, Std, and 95% Confidence Intervals across seeds:
    CI = 2.776 * (std / sqrt(5)) for df=4 at 95% confidence.
    """
    summary_rows = []
    t_crit = 2.776 # Student's t for df=4 (5 seeds), alpha=0.05
    
    for seed_rec in results_list:
        dataset = seed_rec["dataset"]
        seed = seed_rec["seed"]
        
        for setting_key, setting_name in [("setting_a_hard", "Hard Historical Negatives"), ("setting_b_mixed", "Mixed Random Negatives")]:
            models_data = seed_rec[setting_key]
            for model_name, step_list in models_data.items():
                if not step_list: continue
                # Average across transitions for this seed
                avg_f1 = np.mean([s["f1"] for s in step_list])
                avg_prec = np.mean([s["precision"] for s in step_list])
                avg_rec = np.mean([s["recall"] for s in step_list])
                avg_acc = np.mean([s["accuracy"] for s in step_list])
                
                # Ranking area metrics
                valid_rocs = [s["roc_auc"] for s in step_list if isinstance(s.get("roc_auc"), (int, float))]
                avg_roc = np.mean(valid_rocs) if valid_rocs else None
                
                valid_aps = [s["average_precision"] for s in step_list if isinstance(s.get("average_precision"), (int, float))]
                avg_ap = np.mean(valid_aps) if valid_aps else None
                
                summary_rows.append({
                    "dataset": dataset,
                    "setting": setting_name,
                    "model": model_name,
                    "seed": seed,
                    "f1": avg_f1,
                    "precision": avg_prec,
                    "recall": avg_rec,
                    "accuracy": avg_acc,
                    "roc_auc": avg_roc,
                    "average_precision": avg_ap
                })
                
    df_raw = pd.DataFrame(summary_rows)
    
    # Group by dataset, setting, model
    agg_rows = []
    for (d, sett, m), grp in df_raw.groupby(["dataset", "setting", "model"]):
        n_seeds = len(grp)
        f1_mean = grp["f1"].mean()
        f1_std = grp["f1"].std() if n_seeds > 1 else 0.0
        f1_ci = t_crit * (f1_std / math.sqrt(n_seeds)) if n_seeds > 1 else 0.0
        
        p_mean = grp["precision"].mean()
        p_std = grp["precision"].std() if n_seeds > 1 else 0.0
        
        r_mean = grp["recall"].mean()
        r_std = grp["recall"].std() if n_seeds > 1 else 0.0
        
        roc_valid = grp["roc_auc"].dropna()
        roc_str = f"{roc_valid.mean():.4f} ± {roc_valid.std():.4f}" if len(roc_valid) > 0 else "N/A (Discrete)"
        
        ap_valid = grp["average_precision"].dropna()
        ap_str = f"{ap_valid.mean():.4f} ± {ap_valid.std():.4f}" if len(ap_valid) > 0 else "N/A (Discrete)"
        
        agg_rows.append({
            "Dataset": d,
            "Evaluation Setting": sett,
            "Model": m,
            "Seeds": n_seeds,
            "F1 (Mean ± Std)": f"{f1_mean:.2f}% ± {f1_std:.2f}%",
            "F1 95% CI": f"±{f1_ci:.2f}%",
            "Precision (Mean ± Std)": f"{p_mean:.2f}% ± {p_std:.2f}%",
            "Recall (Mean ± Std)": f"{r_mean:.2f}% ± {r_std:.2f}%",
            "ROC-AUC (Mean ± Std)": roc_str,
            "Average Precision (Mean ± Std)": ap_str,
            "F1_mean_num": f1_mean,
            "Precision_mean_num": p_mean,
            "Recall_mean_num": r_mean
        })
        
    return pd.DataFrame(agg_rows)


def main():
    t_start = time.time()
    all_results = []
    
    # 1. Benchmark CIC-IDS2017 (5 daily snapshots, Day 0-2 train, Day 3 val, Day 4 test)
    cic_snaps = load_cic_snapshots()
    cic_results = evaluate_dataset_benchmark("CIC-IDS2017", cic_snaps, train_end_idx=2, val_end_idx=3, seeds=SEEDS)
    all_results.extend(cic_results)
    
    # 2. Benchmark APEX-IDS2026 (44 daily snapshots, train 0-24, val 25-31, test 32-43)
    apex_snaps = load_apex_snapshots()
    apex_results = evaluate_dataset_benchmark("APEX-IDS2026", apex_snaps, train_end_idx=24, val_end_idx=31, seeds=SEEDS)
    all_results.extend(apex_results)
    
    # Save raw structured results
    with open(RAW_RESULTS_FILE, "w") as fp:
        json.dump(all_results, fp, indent=2)
    print(f"\nSaved raw multi-seed benchmark results to {RAW_RESULTS_FILE}")
    
    # Aggregate and generate summary table
    df_summary = aggregate_benchmark_results(all_results)
    df_summary.to_csv(SUMMARY_CSV_FILE, index=False)
    print(f"Saved aggregated benchmark summary to {SUMMARY_CSV_FILE}")
    
    print("\n" + "=" * 80)
    print("FIVE-SEED BENCHMARK COMPLETE (Total Time: {:.1f}s)".format(time.time() - t_start))
    print("=" * 80)
    print(df_summary[["Dataset", "Evaluation Setting", "Model", "F1 (Mean ± Std)", "Precision (Mean ± Std)", "Recall (Mean ± Std)", "ROC-AUC (Mean ± Std)", "Average Precision (Mean ± Std)"]].to_string())


if __name__ == "__main__":
    main()
