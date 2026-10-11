import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# Define paths
BASE_DIR = Path("/Users/kovoordheeraj/Documents/CN Lab CTG")
CSV_PATH = BASE_DIR / "results/metrics/dataset_scope_comparison.csv"
FIG_FINAL_DIR = BASE_DIR / "figures/final_paper"
FIG_CTG_METRICS_DIR = Path("/Users/kovoordheeraj/Documents/CTGMetrics/nrefigures")

FIG_FINAL_DIR.mkdir(parents=True, exist_ok=True)
FIG_CTG_METRICS_DIR.mkdir(parents=True, exist_ok=True)

def save_fig(fig, path_without_ext):
    """Save figure in PNG (300 dpi), PDF, and SVG with tight bbox."""
    fig.savefig(f"{path_without_ext}.png", dpi=300, bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.pdf", bbox_inches='tight')
    fig.savefig(f"{path_without_ext}.svg", bbox_inches='tight')
    print(f"Saved: {path_without_ext}.[png|pdf|svg]")

def generate_dataset_scope_comparison_figures():
    df = pd.read_csv(CSV_PATH)
    
    # Dataset order (APEX first, CIC second, followed by other established datasets)
    datasets = df['Dataset'].tolist()
    y_pos = np.arange(len(datasets))
    
    # Springer / Academic typography and styling setup
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['grid.color'] = '#E0E0E0'
    plt.rcParams['grid.linestyle'] = '--'
    plt.rcParams['grid.alpha'] = 0.7
    
    # Colorblind-safe palette (Wong / Tol inspired)
    c_primary = '#0072B2'   # Blue for APEX-IDS2026
    c_secondary = '#D55E00' # Vermilion for CIC-IDS2017
    c_benchmarks = '#56B4E9'# Sky Blue for other datasets
    c_dark = '#333333'
    
    # Map colors per dataset
    bar_colors = [c_primary if d == 'APEX-IDS2026' else (c_secondary if d == 'CIC-IDS2017' else c_benchmarks) for d in datasets]

    # =========================================================================
    # FIGURE 1: QUANTITATIVE SCOPE (PANELS A & B)
    # Panel A: Dataset Scale (Record count log-scale & Feature count)
    # Panel B: Temporal Duration & Capture Nature
    # =========================================================================
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.8), gridspec_kw={'width_ratios': [1.1, 0.9]})
    
    # ------------------ PANEL A: Dataset Scale ------------------
    records = df['Records_Count'].values
    features = df['Features_Count'].values
    
    bars1 = ax1.barh(y_pos, records, color=bar_colors, height=0.62, edgecolor='black', linewidth=0.6, alpha=0.9, zorder=3)
    ax1.set_xscale('log')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(datasets, fontsize=10, fontweight='bold')
    ax1.invert_yaxis()  # Top-down order
    ax1.set_xlabel('Total Flow / Record Count (Logarithmic Scale)', fontsize=10.5, labelpad=8)
    ax1.set_xlim(1e6, 4e10)
    ax1.grid(True, axis='x', zorder=0)
    ax1.set_title('Panel A: Dataset Scale and Feature Dimensions', fontsize=12, pad=12, loc='left', fontweight='bold')
    
    # Annotate records and feature count on bars
    for i, (b, r, f, unit) in enumerate(zip(bars1, records, features, df['Records_Unit'])):
        if r >= 1e9:
            txt_r = f"{r/1e9:.1f}B records"
        elif r >= 1e6:
            txt_r = f"{r/1e6:.1f}M records"
        else:
            txt_r = f"{r:,.0f}"
        
        feat_str = f"[{f} feat]"
        ax1.text(r * 1.25, i, f"{txt_r}  {feat_str}", va='center', ha='left', fontsize=8.5, color='#222222', fontweight='medium')

    # Legend for Panel A
    legend_elements1 = [
        patches.Patch(facecolor=c_primary, edgecolor='black', label='Primary Benchmark (APEX-IDS2026)'),
        patches.Patch(facecolor=c_secondary, edgecolor='black', label='Secondary Benchmark (CIC-IDS2017)'),
        patches.Patch(facecolor=c_benchmarks, edgecolor='black', label='Established Reference Benchmarks')
    ]
    ax1.legend(handles=legend_elements1, loc='lower right', frameon=True, fontsize=8.5, facecolor='white', framealpha=0.95)

    # ------------------ PANEL B: Temporal Scope ------------------
    days = df['Duration_Days'].values
    continuous = df['Continuous_Capture'].values
    
    bars2 = ax2.barh(y_pos, days, color=bar_colors, height=0.62, edgecolor='black', linewidth=0.6, alpha=0.9, zorder=3)
    ax2.set_xscale('log')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([])  # Shared with left
    ax2.invert_yaxis()
    ax2.set_xlabel('Temporal Duration in Days (Logarithmic Scale)', fontsize=10.5, labelpad=8)
    ax2.set_xlim(0.2, 300)
    ax2.grid(True, axis='x', zorder=0)
    ax2.set_title('Panel B: Temporal Scope and Continuity', fontsize=12, pad=12, loc='left', fontweight='bold')
    
    # Annotate duration text and capture continuity
    for i, (b, d, c, c_type) in enumerate(zip(bars2, days, continuous, df['Capture_Type'])):
        if d >= 30:
            d_txt = f"{d:.0f} d ({d/30:.1f} mo)"
        elif d >= 1:
            d_txt = f"{d:.1f} d"
        else:
            d_txt = f"{d*24:.0f} h"
            
        cont_txt = "Continuous" if c.startswith('Yes') else "Discrete / Discontinuous"
        ax2.text(d * 1.2, i, f"{d_txt} | {cont_txt}", va='center', ha='left', fontsize=8.5, color='#222222', fontweight='medium')

    # Legend for Panel B
    ax2.text(0.98, 0.05, 
             "Note: Discontinuous indicates intermittent collection sessions,\n"
             "selected attack days, or synthetic laboratory batches.",
             transform=ax2.transAxes, ha='right', va='bottom', fontsize=8,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', edgecolor='#CCCCCC', alpha=0.95))

    plt.tight_layout()
    
    # Save Figure 1
    save_fig(fig1, str(FIG_FINAL_DIR / "fig08_dataset_scale_temporal_scope"))
    save_fig(fig1, str(FIG_CTG_METRICS_DIR / "fig08_dataset_scale_temporal_scope"))
    plt.close(fig1)

    # =========================================================================
    # FIGURE 2: QUALITATIVE & CTG SUITABILITY MATRIX (PANELS C & D)
    # Panel C: Temporal and Topology Characteristics
    # Panel D: CTG Analytical Suitability Summary
    # =========================================================================
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(16, 7.2), gridspec_kw={'width_ratios': [1.05, 1.05]})
    
    # Status styling maps for matrix
    # Rating values: 'Yes' (High), 'Partial' (Moderate), 'No' (Low), 'Not verified'
    status_colors = {
        'Yes': '#2CA02C',      # Forest Green
        'High': '#2CA02C',
        'Partial': '#FF7F0E',  # Amber / Orange
        'Moderate': '#FF7F0E',
        'No': '#D62728',       # Crimson
        'Low': '#D62728',
        'Not verified': '#7F7F7F' # Slate Gray
    }
    status_markers = {
        'Yes': '● Yes',
        'High': '● High',
        'Partial': '◑ Partial',
        'Moderate': '◑ Mod.',
        'No': '○ No',
        'Low': '○ Low',
        'Not verified': '◌ Unver.'
    }

    # ------------------ PANEL C: Temporal & Topology Matrix ------------------
    cols_c = [
        'Timestamps', 
        'Endpoints', 
        'Chronological_Ordering', 
        'Repeated_Observations', 
        'Attack_Labels', 
        'Real_Traffic_Evidence'
    ]
    col_labels_c = [
        'Timestamps\nDocumented',
        'Endpoint IDs\n(Src/Dst IPs)',
        'Chronological\nOrdering',
        'Repeated\nObservations',
        'Attack\nLabels',
        'Real Traffic\nEvidence'
    ]
    
    ax3.set_xlim(-0.5, len(cols_c) - 0.5)
    ax3.set_ylim(-0.5, len(datasets) - 0.5)
    ax3.set_xticks(np.arange(len(cols_c)))
    ax3.set_xticklabels(col_labels_c, fontsize=9.5, fontweight='bold', rotation=0, ha='center')
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(datasets, fontsize=10, fontweight='bold')
    ax3.invert_yaxis()
    ax3.set_title('Panel C: Temporal & Network-Topology Suitability Criteria', fontsize=11.5, pad=14, loc='left', fontweight='bold')
    
    # Draw grid boxes and status tags for Panel C
    for i, row in df.iterrows():
        for j, col in enumerate(cols_c):
            val = str(row[col])
            # Determine canonical status
            if val.startswith('Yes'):
                key = 'Yes'
            elif val.startswith('Partial'):
                key = 'Partial'
            elif val.startswith('No'):
                key = 'No'
            else:
                key = 'Not verified'
                
            color = status_colors[key]
            text_label = status_markers[key]
            
            # Subtle cell background
            bg_color = '#EAF5EA' if key == 'Yes' else ('#FEF3E8' if key == 'Partial' else '#FCEBEB')
            rect = patches.Rectangle((j - 0.47, i - 0.42), 0.94, 0.84, linewidth=0.8, edgecolor='#D0D0D0', facecolor=bg_color)
            ax3.add_patch(rect)
            
            # Text inside cell
            ax3.text(j, i, text_label, ha='center', va='center', fontsize=9, color=color, fontweight='bold')

    # Remove outer ticks
    ax3.tick_params(left=False, bottom=False)

    # ------------------ PANEL D: CTG Analytical Suitability Summary ------------------
    cols_d = [
        'CTG_Temporal_Graph_Suitability',
        'CTG_Endpoint_Level_Suitability',
        'CTG_Chronological_Split_Suitability',
        'CTG_Attack_Label_Suitability',
        'CTG_Scale_Suitability'
    ]
    col_labels_d = [
        'Temporal Graph\nConstruction',
        'Endpoint-Level\nResolution',
        'Chronological\nTrain/Val/Test',
        'Attack-Label\nIntegrity',
        'Dataset Scale\n& Realism'
    ]
    
    ax4.set_xlim(-0.5, len(cols_d) - 0.5)
    ax4.set_ylim(-0.5, len(datasets) - 0.5)
    ax4.set_xticks(np.arange(len(cols_d)))
    ax4.set_xticklabels(col_labels_d, fontsize=9.5, fontweight='bold', rotation=0, ha='center')
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels([]) # Shared with Panel C
    ax4.invert_yaxis()
    ax4.set_title('Panel D: CTG Analytical Suitability Matrix & Role', fontsize=11.5, pad=14, loc='left', fontweight='bold')
    
    # Draw grid boxes and status tags for Panel D
    for i, row in df.iterrows():
        for j, col in enumerate(cols_d):
            val = str(row[col])
            if val.startswith('High'):
                key = 'High'
            elif val.startswith('Moderate'):
                key = 'Moderate'
            elif val.startswith('Low'):
                key = 'Low'
            else:
                key = 'Not verified'
                
            color = status_colors[key]
            text_label = status_markers[key]
            
            bg_color = '#EAF5EA' if key == 'High' else ('#FEF3E8' if key == 'Moderate' else '#FCEBEB')
            rect = patches.Rectangle((j - 0.47, i - 0.42), 0.94, 0.84, linewidth=0.8, edgecolor='#D0D0D0', facecolor=bg_color)
            ax4.add_patch(rect)
            
            ax4.text(j, i, text_label, ha='center', va='center', fontsize=9, color=color, fontweight='bold')

    ax4.tick_params(left=False, bottom=False)

    # Shared Legend for Panels C & D
    legend_handles = [
        patches.Patch(facecolor='#EAF5EA', edgecolor='#2CA02C', label='Yes / High: Fully documented and verified directly'),
        patches.Patch(facecolor='#FEF3E8', edgecolor='#FF7F0E', label='Partial / Mod: Documented with qualifications or requires preprocessing'),
        patches.Patch(facecolor='#FCEBEB', edgecolor='#D62728', label='No / Low: Not supported, omitted, or unverified in standard format'),
        patches.Patch(facecolor='#F5F5F5', edgecolor='#7F7F7F', label='Not verified: Authoritative documentation absent or unverified')
    ]
    fig2.legend(handles=legend_handles, loc='lower center', ncol=2, frameon=True, fontsize=9, 
                facecolor='white', framealpha=0.95, edgecolor='#CCCCCC', bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    # Save Figure 2
    save_fig(fig2, str(FIG_FINAL_DIR / "fig09_dataset_topology_ctg_suitability"))
    save_fig(fig2, str(FIG_CTG_METRICS_DIR / "fig09_dataset_topology_ctg_suitability"))
    plt.close(fig2)

    # =========================================================================
    # FIGURE 3: UNIFIED COMBINED 4-PANEL FIGURE (FOR JOURNAL SUBMISSION)
    # A single 2x2 multi-panel layout combining Panels A, B, C, D
    # =========================================================================
    fig_comb = plt.figure(figsize=(18, 14))
    gs = fig_comb.add_gridspec(2, 2, height_ratios=[1, 1.25], hspace=0.28, wspace=0.18)
    
    ax_a = fig_comb.add_subplot(gs[0, 0])
    ax_b = fig_comb.add_subplot(gs[0, 1])
    ax_c = fig_comb.add_subplot(gs[1, 0])
    ax_d = fig_comb.add_subplot(gs[1, 1])

    # Re-plot Panel A
    bars_a = ax_a.barh(y_pos, records, color=bar_colors, height=0.62, edgecolor='black', linewidth=0.6, alpha=0.9, zorder=3)
    ax_a.set_xscale('log')
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(datasets, fontsize=9.5, fontweight='bold')
    ax_a.invert_yaxis()
    ax_a.set_xlabel('Total Flow / Record Count (Log Scale)', fontsize=10, labelpad=6)
    ax_a.set_xlim(1e6, 4e10)
    ax_a.grid(True, axis='x', zorder=0)
    ax_a.set_title('(A) Dataset Scale and Feature Dimensions', fontsize=11.5, pad=10, loc='left', fontweight='bold')
    for i, (r, f) in enumerate(zip(records, features)):
        txt_r = f"{r/1e9:.1f}B" if r >= 1e9 else (f"{r/1e6:.1f}M" if r >= 1e6 else f"{r:,.0f}")
        ax_a.text(r * 1.25, i, f"{txt_r} [{f} feat]", va='center', ha='left', fontsize=8.5, color='#222222', fontweight='medium')

    # Re-plot Panel B
    bars_b = ax_b.barh(y_pos, days, color=bar_colors, height=0.62, edgecolor='black', linewidth=0.6, alpha=0.9, zorder=3)
    ax_b.set_xscale('log')
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels([])
    ax_b.invert_yaxis()
    ax_b.set_xlabel('Temporal Duration in Days (Log Scale)', fontsize=10, labelpad=6)
    ax_b.set_xlim(0.2, 300)
    ax_b.grid(True, axis='x', zorder=0)
    ax_b.set_title('(B) Temporal Scope and Capture Continuity', fontsize=11.5, pad=10, loc='left', fontweight='bold')
    for i, (d, c) in enumerate(zip(days, continuous)):
        d_txt = f"{d:.0f} d ({d/30:.1f} mo)" if d >= 30 else (f"{d:.1f} d" if d >= 1 else f"{d*24:.0f} h")
        cont_txt = "Continuous" if c.startswith('Yes') else "Discrete / Intermittent"
        ax_b.text(d * 1.2, i, f"{d_txt} | {cont_txt}", va='center', ha='left', fontsize=8.5, color='#222222', fontweight='medium')

    # Re-plot Panel C
    ax_c.set_xlim(-0.5, len(cols_c) - 0.5)
    ax_c.set_ylim(-0.5, len(datasets) - 0.5)
    ax_c.set_xticks(np.arange(len(cols_c)))
    ax_c.set_xticklabels(col_labels_c, fontsize=8.5, fontweight='bold', ha='center')
    ax_c.set_yticks(y_pos)
    ax_c.set_yticklabels(datasets, fontsize=9.5, fontweight='bold')
    ax_c.invert_yaxis()
    ax_c.set_title('(C) Temporal & Network-Topology Properties', fontsize=11.5, pad=10, loc='left', fontweight='bold')
    for i, row in df.iterrows():
        for j, col in enumerate(cols_c):
            val = str(row[col])
            key = 'Yes' if val.startswith('Yes') else ('Partial' if val.startswith('Partial') else ('No' if val.startswith('No') else 'Not verified'))
            bg_color = '#EAF5EA' if key == 'Yes' else ('#FEF3E8' if key == 'Partial' else '#FCEBEB')
            rect = patches.Rectangle((j - 0.47, i - 0.42), 0.94, 0.84, linewidth=0.8, edgecolor='#D0D0D0', facecolor=bg_color)
            ax_c.add_patch(rect)
            ax_c.text(j, i, status_markers[key], ha='center', va='center', fontsize=8.5, color=status_colors[key], fontweight='bold')
    ax_c.tick_params(left=False, bottom=False)

    # Re-plot Panel D
    ax_d.set_xlim(-0.5, len(cols_d) - 0.5)
    ax_d.set_ylim(-0.5, len(datasets) - 0.5)
    ax_d.set_xticks(np.arange(len(cols_d)))
    ax_d.set_xticklabels(col_labels_d, fontsize=8.5, fontweight='bold', ha='center')
    ax_d.set_yticks(y_pos)
    ax_d.set_yticklabels([])
    ax_d.invert_yaxis()
    ax_d.set_title('(D) CTG Analytical Suitability Matrix', fontsize=11.5, pad=10, loc='left', fontweight='bold')
    for i, row in df.iterrows():
        for j, col in enumerate(cols_d):
            val = str(row[col])
            key = 'High' if val.startswith('High') else ('Moderate' if val.startswith('Moderate') else ('Low' if val.startswith('Low') else 'Not verified'))
            bg_color = '#EAF5EA' if key == 'High' else ('#FEF3E8' if key == 'Moderate' else '#FCEBEB')
            rect = patches.Rectangle((j - 0.47, i - 0.42), 0.94, 0.84, linewidth=0.8, edgecolor='#D0D0D0', facecolor=bg_color)
            ax_d.add_patch(rect)
            ax_d.text(j, i, status_markers[key], ha='center', va='center', fontsize=8.5, color=status_colors[key], fontweight='bold')
    ax_d.tick_params(left=False, bottom=False)

    # Global legend for unified figure
    unified_legend_handles = [
        patches.Patch(facecolor=c_primary, edgecolor='black', label='Primary Benchmark (APEX-IDS2026)'),
        patches.Patch(facecolor=c_secondary, edgecolor='black', label='Secondary Benchmark (CIC-IDS2017)'),
        patches.Patch(facecolor='#EAF5EA', edgecolor='#2CA02C', label='Status: Yes / High'),
        patches.Patch(facecolor='#FEF3E8', edgecolor='#FF7F0E', label='Status: Partial / Moderate'),
        patches.Patch(facecolor='#FCEBEB', edgecolor='#D62728', label='Status: No / Low')
    ]
    fig_comb.legend(handles=unified_legend_handles, loc='lower center', ncol=5, frameon=True, fontsize=9.5,
                    facecolor='white', framealpha=0.95, edgecolor='#CCCCCC', bbox_to_anchor=(0.5, 0.01))

    save_fig(fig_comb, str(FIG_FINAL_DIR / "fig10_dataset_scope_comparison_unified"))
    save_fig(fig_comb, str(FIG_CTG_METRICS_DIR / "fig10_dataset_scope_comparison_unified"))
    plt.close(fig_comb)

    print("All dataset scope comparison figures generated successfully.")

if __name__ == "__main__":
    generate_dataset_scope_comparison_figures()
