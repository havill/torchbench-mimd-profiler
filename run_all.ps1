# run_all.ps1
$devices = @("cpu", "cuda")
$batch_sizes = @(1, 8, 16, 32)
$burn_time = 10.0
$script_name = "mimd-benchmark.py"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 STARTING AUTOMATED BENCHMARK SUITE" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

foreach ($dev in $devices) {
    foreach ($bs in $batch_sizes) {
        Write-Host "`n>>> Starting Run: Device = $dev | Batch Size = $bs | Time = ${burn_time}s" -ForegroundColor Yellow
        
        # Execute the python script with the parameters
        python $script_name -d $dev -b $bs -t $burn_time
        
        # Optional: Sleep for 5 seconds between heavy GPU runs to let thermals reset
        if ($dev -eq "cuda") {
            Write-Host "Cooling down for 5 seconds..." -ForegroundColor DarkGray
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host "`n✅ ALL BENCHMARKS COMPLETE! Check your directory for the CSV files." -ForegroundColor Green