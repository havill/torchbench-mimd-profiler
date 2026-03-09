#!/bin/bash
# run_all.sh

# --- 1. LISTEN FOR TERMINAL ARGUMENTS ---
DIR=""
DEVICES_INPUT="cpu,cuda" # Default to both

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dir) DIR="$2"; shift ;;
        -d|--device) DEVICES_INPUT="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Convert the comma-separated string into a bash array
IFS=',' read -r -a DEVICES <<< "$DEVICES_INPUT"

BATCH_SIZES=(1 8 16 32)
BURN_TIME=10.0
SCRIPT_NAME="mimd-benchmarks.py"

echo -e "\e[1;36m==================================================\e[0m"
echo -e "\e[1;36m🚀 STARTING AUTOMATED BENCHMARK SUITE\e[0m"
echo -e "\e[1;36m==================================================\e[0m"

for dev in "${DEVICES[@]}"; do
    # Strip any accidental whitespace
    dev=$(echo "$dev" | xargs)
    
    for bs in "${BATCH_SIZES[@]}"; do
        echo -e "\n\e[1;33m>>> Starting Run: Device = $dev | Batch Size = $bs | Time = ${BURN_TIME}s\e[0m"
        
        # --- 2. BUILD THE COMMAND SAFELY ---
        ARGS=("-d" "$dev" "-b" "$bs" "-t" "$BURN_TIME")
        
        if [ -n "$DIR" ]; then
            ARGS+=("--dir" "$DIR")
        fi
        
        # --- 3. EXECUTE ---
        python3 "$SCRIPT_NAME" "${ARGS[@]}"
        
        if [ "$dev" == "cuda" ]; then
            echo -e "\e[90mCooling down for 5 seconds...\e[0m"
            sleep 5
        fi
    done
done

echo -e "\n\e[1;32m✅ ALL BENCHMARKS COMPLETE! Check your directory for the CSV files.\e[0m"