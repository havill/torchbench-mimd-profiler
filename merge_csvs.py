import glob
import csv
import os
import argparse

def merge_results(target_dir="."):
    print("--- 📊 Benchmark Data Merger ---")
    
    # Resolve the target directory to an absolute path for cleaner output
    target_dir = os.path.abspath(target_dir)
    print(f"📂 Scanning directory: {target_dir}")
    
    # 1. Look for all CSVs that match our naming convention in the target directory
    file_pattern = os.path.join(target_dir, "hardware_profiling_*.csv")
    csv_files = glob.glob(file_pattern)
    
    if not csv_files:
        print("❌ No benchmark CSV files found in this directory.")
        return

    print(f"🔍 Found {len(csv_files)} result files. Merging...")
    
    master_filename = os.path.join(target_dir, "master_benchmark_results.csv")
    total_rows = 0
    
    # 2. Open our new master file to write into
    with open(master_filename, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # 3. Loop through every individual file
        for index, file in enumerate(csv_files):
            with open(file, mode='r', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                
                # Extract the header row
                try:
                    headers = next(reader)
                except StopIteration:
                    continue # Skip empty files
                
                # Write the header ONLY for the very first file
                if index == 0:
                    writer.writerow(headers)
                    
                # Append all the actual data rows
                for row in reader:
                    writer.writerow(row)
                    total_rows += 1
                    
    print(f"✅ Successfully merged {total_rows} benchmark runs into:")
    print(f"   📁 {master_filename}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge TorchBench profiling CSVs into a master file.")
    parser.add_argument(
        "-d", "--dir", 
        type=str, 
        default=".", 
        help="Directory containing the CSV files to merge (defaults to current directory)."
    )
    args = parser.parse_args()
    
    merge_results(args.dir)