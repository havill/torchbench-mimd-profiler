import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse

def generate_charts(csv_file="master_benchmark_results.csv"):
    # Resolve the absolute path so we know exactly where to save the images
    csv_file = os.path.abspath(csv_file)
    out_dir = os.path.dirname(csv_file)
    
    print(f"--- 📊 Generating Charts from {csv_file} ---")
    
    if not os.path.exists(csv_file):
        print(f"❌ Error: Could not find {csv_file}. Run the merge script first or specify the correct path with -f.")
        return

    # 1. Load the data
    df = pd.read_csv(csv_file)

    # 2. Clean the data (Drop failed runs and convert string numbers to floats)
    df = df[df['Status'] == 'Passed'].copy()
    
    numeric_cols = ['Throughput_passes_per_sec', 'Latency_ms', 'Efficiency_GFLOPs_per_W']
    for col in numeric_cols:
        # Force conversion to numeric, turning "N/A" into NaN, then fill with 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Convert Batch_Size to string so it graphs nicely as a categorical label
    df['Batch_Size'] = df['Batch_Size'].astype(str)

    # Set the visual style
    sns.set_theme(style="whitegrid")

    # ==========================================
    # CHART 1: Throughput (CPU vs CUDA)
    # ==========================================
    print("📈 Generating Throughput Comparison Chart...")
    plt.figure(figsize=(12, 6))
    
    chart1 = sns.catplot(
        data=df, kind="bar",
        x="Batch_Size", y="Throughput_passes_per_sec", hue="Backend", col="Model",
        height=5, aspect=0.8, palette="muted", sharey=False
    )
    chart1.set_axis_labels("Batch Size", "Throughput (Passes / Sec)")
    chart1.fig.suptitle("Hardware Throughput by Model and Batch Size", y=1.05)
    
    # Save the chart in the same directory as the CSV
    out_file1 = os.path.join(out_dir, "chart_throughput_comparison.png")
    chart1.savefig(out_file1, dpi=300, bbox_inches="tight")
    print(f"   ✅ Saved: {out_file1}")

    # ==========================================
    # CHART 2: Energy Efficiency (CUDA Only)
    # ==========================================
    print("🔋 Generating Energy Efficiency Chart...")
    
    cuda_df = df[(df['Backend'] == 'cuda') & (df['Efficiency_GFLOPs_per_W'] > 0)]
    
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
        
        # Save the chart in the same directory as the CSV
        out_file2 = os.path.join(out_dir, "chart_energy_efficiency.png")
        plt.savefig(out_file2, dpi=300)
        print(f"   ✅ Saved: {out_file2}")
    else:
        print("   ⚠️ Skipped Energy chart (No valid CUDA power data found).")

    print("\n🎉 All charts generated successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate charts from a master benchmark CSV.")
    parser.add_argument(
        "-f", "--file", 
        type=str, 
        default="master_benchmark_results.csv", 
        help="Path to the master CSV file (defaults to 'master_benchmark_results.csv' in current dir)."
    )
    args = parser.parse_args()
    
    generate_charts(args.file)