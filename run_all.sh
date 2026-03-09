#!/bin/bash

# run_all.sh
DEVICES=("cpu" "cuda")
BATCH_SIZES=(1 8 16 32)
BURN_TIME=10.0
SCRIPT_NAME="mimd-benchmark.py"

echo -e "\e[1;36m==================================================\e[0m"
echo -e "\e[1;36m🚀 STARTING AUTOMATED BENCHMARK SUITE\e[0m"
echo -e "\e[1;36m==================================================\e[0m"

for dev in "${DEVICES[@]}"; do
    for bs in "${BATCH_SIZES[@]}"; do
        echo -e "\n\e[1;33m>>> Starting Run: Device = $dev | Batch Size = $bs | Time = ${BURN_TIME}s\e[0m"
        
        # Execute the python script
        python3 $SCRIPT_NAME -d "$dev" -b "$bs" -t "$BURN_TIME"
        
        # Optional: Sleep for 5 seconds between heavy GPU runs to let thermals reset
        if [ "$dev" == "cuda" ]; then
            echo -e "\e[90mCooling down for 5 seconds...\e[0m"
            sleep 5
        fi
    done
done

echo -e "\n\e[1;32m✅ ALL BENCHMARKS COMPLETE! Check your directory for the CSV files.\e[0m"