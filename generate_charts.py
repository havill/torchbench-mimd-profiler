import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse

def generate_charts(csv_file="000.combined-ALL.csv", filter_model=None, filter_backend=None, interactive=False, export_formats=["png"]):
    # Resolve the absolute path so we know exactly where to save the images
    csv_file = os.path.abspath(csv_file)
    out_dir = os.path.dirname(csv_file)
    
    print(f"--- 📊 Generating Charts from {csv_file} ---")
    
    if not os.path.exists(csv_file):
        print(f"❌ Error: Could not find {csv_file}. Run the merge script first or specify the correct path with -f.")
        return

    # 1. Load the data
    df = pd.read_csv(csv_file)

    # Separate passed and failed runs
    df_passed = df[df['Status'] == 'Passed'].copy()
    df_failed = df[df['Status'] != 'Passed'].copy()

    numeric_cols = ['Throughput_passes_per_sec', 'Latency_ms', 'Efficiency_GFLOPs_per_W']
    for col in numeric_cols:
        df_passed[col] = pd.to_numeric(df_passed[col], errors='coerce').fillna(0)
        if not df_failed.empty:
            df_failed[col] = pd.to_numeric(df_failed[col], errors='coerce').fillna(0)

    df_passed['Batch_Size'] = df_passed['Batch_Size'].astype(str)
    if not df_failed.empty:
        df_failed['Batch_Size'] = df_failed['Batch_Size'].astype(str)

    # Filtering
    if filter_model:
        df_passed = df_passed[df_passed['Model'] == filter_model]
        if not df_failed.empty:
            df_failed = df_failed[df_failed['Model'] == filter_model]
    if filter_backend:
        df_passed = df_passed[df_passed['Backend'] == filter_backend]
        if not df_failed.empty:
            df_failed = df_failed[df_failed['Backend'] == filter_backend]

    # Set the visual style
    sns.set_theme(style="whitegrid")

    # ==========================================
    # CHART 1: Throughput (CPU vs CUDA)
    # ==========================================
    print("📈 Generating Throughput Comparison Chart...")
    plt.figure(figsize=(12, 6))
    chart1 = sns.catplot(
        data=df_passed, kind="bar",
        x="Batch_Size", y="Throughput_passes_per_sec", hue="Backend", col="Model",
        height=5, aspect=0.8, palette="muted", sharey=False
    )
    chart1.set_axis_labels("Batch Size", "Throughput (Passes / Sec)")
    chart1.fig.suptitle("Hardware Throughput by Model and Batch Size", y=1.05)
    # Add summary stats
    for ax in chart1.axes.flat:
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(f'{height:.2f}', (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='bottom', fontsize=8, color='black')
    for fmt in export_formats:
        out_file1 = os.path.join(out_dir, f"chart_throughput_comparison.{fmt}")
        chart1.savefig(out_file1, dpi=300, bbox_inches="tight")
        print(f"   ✅ Saved: {out_file1}")

    # ==========================================
    # CHART 2: Energy Efficiency (CUDA Only)
    # ==========================================
    print("🔋 Generating Energy Efficiency Chart...")
    cuda_df = df_passed[(df_passed['Backend'] == 'cuda') & (df_passed['Efficiency_GFLOPs_per_W'] > 0)]
    if not cuda_df.empty:
        plt.figure(figsize=(10, 6))
        chart2 = sns.barplot(
            data=cuda_df, 
            x="Model", y="Efficiency_GFLOPs_per_W", hue="Batch_Size", 
            palette="viridis"
        )
        plt.title("Hardware Energy Efficiency Scaling", fontsize=14)
        plt.ylabel("Efficiency (GFLOPs / Watt)", fontsize=12)
        plt.xlabel("Model", fontsize=12)
        plt.legend(title='Batch Size')
        plt.tight_layout()
        # Add summary stats
        for p in chart2.patches:
            height = p.get_height()
            chart2.annotate(f'{height:.2f}', (p.get_x() + p.get_width() / 2., height),
                           ha='center', va='bottom', fontsize=8, color='black')
        for fmt in export_formats:
            out_file2 = os.path.join(out_dir, f"chart_energy_efficiency.{fmt}")
            plt.savefig(out_file2, dpi=300)
            print(f"   ✅ Saved: {out_file2}")
    else:
        print("   ⚠️ Skipped Energy chart (No valid CUDA power data found).")

    # ==========================================
    # CHART 3: Latency (Boxplot)
    # ==========================================
    print("⏱️ Generating Latency Chart...")
    if not df_passed.empty:
        plt.figure(figsize=(12, 6))
        chart3 = sns.boxplot(
            data=df_passed,
            x="Batch_Size", y="Latency_ms", hue="Backend", palette="Set2"
        )
        plt.title("Latency Distribution by Batch Size and Backend", fontsize=14)
        plt.ylabel("Latency (ms)", fontsize=12)
        plt.xlabel("Batch Size", fontsize=12)
        plt.legend(title='Backend')
        plt.tight_layout()
        # Add mean/median lines
        means = df_passed.groupby(['Batch_Size', 'Backend'])['Latency_ms'].mean().reset_index()
        for idx, row in means.iterrows():
            plt.annotate(f"Mean: {row['Latency_ms']:.2f}",
                         xy=(idx, row['Latency_ms']),
                         xytext=(idx, row['Latency_ms']+5),
                         arrowprops=dict(facecolor='black', shrink=0.05),
                         fontsize=8, color='black')
        for fmt in export_formats:
            out_file3 = os.path.join(out_dir, f"chart_latency_boxplot.{fmt}")
            plt.savefig(out_file3, dpi=300)
            print(f"   ✅ Saved: {out_file3}")

    # ==========================================
    # CHART 4: Error Rate Visualization
    # ==========================================
    print("❌ Generating Error Rate Chart...")
    if not df_failed.empty:
        plt.figure(figsize=(10, 6))
        error_counts = df_failed.groupby(['Model', 'Backend']).size().reset_index(name='Error_Count')
        chart4 = sns.barplot(
            data=error_counts,
            x="Model", y="Error_Count", hue="Backend", palette="Reds"
        )
        plt.title("Failed Runs by Model and Backend", fontsize=14)
        plt.ylabel("Error Count", fontsize=12)
        plt.xlabel("Model", fontsize=12)
        plt.legend(title='Backend')
        plt.tight_layout()
        for fmt in export_formats:
            out_file4 = os.path.join(out_dir, f"chart_error_rate.{fmt}")
            plt.savefig(out_file4, dpi=300)
            print(f"   ✅ Saved: {out_file4}")
    else:
        print("   ⚠️ No failed runs to visualize.")

    # ==========================================
    # CHART 5: Interactive Charts (Plotly)
    # ==========================================
    if interactive:
        try:
            import plotly.express as px
            print("🖱️ Generating Interactive Throughput Chart...")
            fig = px.bar(df_passed, x="Batch_Size", y="Throughput_passes_per_sec", color="Backend", facet_col="Model",
                         title="Interactive Throughput by Model and Batch Size")
            fig.write_html(os.path.join(out_dir, "chart_throughput_interactive.html"))
            print(f"   ✅ Saved: {os.path.join(out_dir, 'chart_throughput_interactive.html')}")
        except ImportError:
            print("   ⚠️ Plotly not installed. Skipping interactive chart.")

    print("\n🎉 All charts generated successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate charts from a master benchmark CSV.")
    parser.add_argument(
        "-f", "--file", 
        type=str, 
        default="000.combined-ALL.csv", 
        help="Path to the master CSV file (defaults to '000.combined-ALL.csv' in current dir)."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Filter charts to a specific model (optional)."
    )
    parser.add_argument(
        "-b", "--backend",
        type=str,
        default=None,
        help="Filter charts to a specific backend (optional)."
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Generate interactive charts (requires Plotly)."
    )
    parser.add_argument(
        "-x", "--export-formats",
        type=str,
        default="png",
        help="Comma-separated list of export formats (e.g., png,pdf,svg)."
    )
    args = parser.parse_args()
    export_formats = [fmt.strip() for fmt in args.export_formats.split(",") if fmt.strip()]
    filter_model = args.model
    filter_backend = args.backend
    interactive = args.interactive
    generate_charts(
        csv_file=args.file,
        filter_model=filter_model,
        filter_backend=filter_backend,
        interactive=interactive,
        export_formats=export_formats
    )