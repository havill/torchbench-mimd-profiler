import glob
import csv
import os

def merge_results():
    print("--- 📊 Benchmark Data Merger ---")
    
    # 1. Look for all CSVs that match our script's naming convention
    file_pattern = "hardware_profiling_*.csv"
    csv_files = glob.glob(file_pattern)
    
    if not csv_files:
        print("❌ No benchmark CSV files found in this directory.")
        return

    print(f"🔍 Found {len(csv_files)} result files. Merging...")
    
    master_filename = "master_benchmark_results.csv"
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
    print(f"   📁 {os.path.abspath(master_filename)}\n")

if __name__ == "__main__":
    merge_results()