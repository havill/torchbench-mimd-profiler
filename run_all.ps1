# run_all.ps1
$devices = @("cpu", "cuda")
$batch_sizes = @(1, 8, 16, 32)
$burn_time = 10.0
$script_name = "mimd-benchmark.py"

# --- NEW: Set your manual TorchBench path here, or leave as "" for auto-discovery ---
$BENCHMARK_DIR = "" # Example: "C:\Users\havil\github.com\benchmark"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING AUTOMATED BENCHMARK SUITE" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

foreach ($dev in $devices) {
    foreach ($bs in $batch_sizes) {
        Write-Host "`n>>> Starting Run: Device = $dev | Batch Size = $bs | Time = ${burn_time}s" -ForegroundColor Yellow
        
        # Build the command arguments safely
        $pyArgs = @("-d", $dev, "-b", $bs, "-t", $burn_time)
        if (![string]::IsNullOrWhiteSpace($BENCHMARK_DIR)) {
            $pyArgs += "--dir"
            $pyArgs += $BENCHMARK_DIR
        }
        
        # Execute the python script with the arguments array
        & python $script_name @pyArgs
        
        # Optional: Sleep for 5 seconds between heavy GPU runs to let thermals reset
        if ($dev -eq "cuda") {
            Write-Host "Cooling down for 5 seconds..." -ForegroundColor DarkGray
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host "`n✅ ALL BENCHMARKS COMPLETE! Check your directory for the CSV files." -ForegroundColor Green