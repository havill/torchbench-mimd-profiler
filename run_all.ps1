# run_all.ps1

# --- 1. LISTEN FOR TERMINAL ARGUMENTS ---
param (
    [string]$Dir = ""
)

$devices = @("cpu", "cuda")
$batch_sizes = @(1, 8, 16, 32)
$burn_time = 10.0
$script_name = "mimd-benchmarks.py" # (Ensured the 's' is here!)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING AUTOMATED BENCHMARK SUITE" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

foreach ($dev in $devices) {
    foreach ($bs in $batch_sizes) {
        Write-Host "`n>>> Starting Run: Device = $dev | Batch Size = $bs | Time = ${burn_time}s" -ForegroundColor Yellow
        
        # --- 2. BUILD THE COMMAND SAFELY ---
        $pyArgs = @("-d", $dev, "-b", $bs, "-t", $burn_time)
        
        # If you passed a -Dir argument, append it to the Python command
        if (![string]::IsNullOrWhiteSpace($Dir)) {
            $pyArgs += "--dir"
            $pyArgs += $Dir
        }
        
        # --- 3. EXECUTE ---
        & python $script_name @pyArgs
        
        # Optional: Sleep for 5 seconds between heavy GPU runs
        if ($dev -eq "cuda") {
            Write-Host "Cooling down for 5 seconds..." -ForegroundColor DarkGray
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host "`n✅ ALL BENCHMARKS COMPLETE! Check your directory for the CSV files." -ForegroundColor Green