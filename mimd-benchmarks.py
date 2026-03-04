import os
import time
import threading
import importlib
import csv
import argparse
from datetime import datetime
import torch

# Gracefully check for the PyTorch FLOP counter
try:
    from torch.utils.flop_counter import FlopCounterMode
    HAS_FLOP_COUNTER = True
except ImportError:
    HAS_FLOP_COUNTER = False

# The "Mount Rushmore" of MIMD/SIMD benchmarks
MIMD_MODELS = ["dlrm", "soft_actor_critic", "BERT_pytorch", "llama"]

# Safe import for NVML (only strictly needed if using CUDA)
try:
    import pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

class PowerMonitor(threading.Thread):
    """Background thread to poll the GPU power sensor via NVML."""
    def __init__(self, device_index=0):
        super().__init__()
        self.keep_running = True
        self.readings = []
        self.valid = False
        if HAS_NVML:
            try:
                pynvml.nvmlInit()
                self.handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
                self.valid = True
            except pynvml.NVMLError:
                pass
        
    def run(self):
        if not self.valid: return
        while self.keep_running:
            try:
                power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
                self.readings.append(power_mw / 1000.0)
            except pynvml.NVMLError:
                pass
            time.sleep(0.01) # Sample every 10ms
            
    def stop(self):
        self.keep_running = False
        if self.valid:
            try: pynvml.nvmlShutdown() 
            except: pass
        if not self.readings: 
            return 0.0, 0.0
        avg_power = sum(self.readings) / len(self.readings)
        peak_power = max(self.readings)
        return avg_power, peak_power


def sync_device(device):
    """Dynamically synchronize based on the target hardware backend."""
    if device == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize()
    elif device == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        torch.mps.synchronize()
    elif device == "xpu" and hasattr(torch, "xpu") and torch.xpu.is_available():
        torch.xpu.synchronize()
    # CPUs run synchronously by default in PyTorch, so they don't need a sync call


def run_unified_stats(device):
    print(f"--- Running MIMD Suite on {device.upper()} (Hardware Profiling + CSV Export) ---")
    
    csv_data = []

    for model_name in MIMD_MODELS:
        print(f"\n[ANALYZING]: {model_name}...", flush=True)
        
        row = {
            "Model": model_name,
            "Backend": device,
            "Status": "Failed",
            "Latency_ms": "N/A",
            "Throughput_passes_per_sec": "N/A",
            "Workload_TFLOPs": "N/A",
            "Avg_Power_W": "N/A",
            "Peak_Power_W": "N/A",
            "Efficiency_GFLOPs_per_W": "N/A",
            "Error_Message": ""
        }
        
        try:
            # 1. Initialize the TorchBench model on the requested device
            module = importlib.import_module(f"torchbenchmark.models.{model_name}")
            model_obj = module.Model(device=device, test="eval")
            
            with torch.no_grad():
                # 2. Measure Workload (FLOPs)
                tflops = 0.0
                if HAS_FLOP_COUNTER:
                    flop_counter = FlopCounterMode(display=False)
                    with flop_counter:
                        model_obj.invoke()
                    total_flops = flop_counter.get_total_flops()
                    tflops = total_flops / 1e12  
                
                # 3. Measure Latency dynamically
                for _ in range(3): # Warmup
                    model_obj.invoke()
                sync_device(device)
                
                # Use CUDA Events for NVIDIA, and Python Perf Counter for CPU/MPS/XPU
                if device == "cuda":
                    start_event = torch.cuda.Event(enable_timing=True)
                    end_event = torch.cuda.Event(enable_timing=True)
                    start_event.record()
                    for _ in range(10): model_obj.invoke()
                    end_event.record()
                    sync_device(device) 
                    avg_latency_ms = start_event.elapsed_time(end_event) / 10.0
                else:
                    t0 = time.perf_counter()
                    for _ in range(10): model_obj.invoke()
                    sync_device(device)
                    t1 = time.perf_counter()
                    avg_latency_ms = ((t1 - t0) * 1000.0) / 10.0
                
                # 4. Measure Power & Throughput
                monitor = None
                if device == "cuda":
                    monitor = PowerMonitor()
                    monitor.start()
                
                start_time = time.time()
                iterations = 0
                while time.time() - start_time < 2.0:
                    model_obj.invoke()
                    sync_device(device)
                    iterations += 1
                    
                if device == "cuda" and monitor:
                    avg_power, peak_power = monitor.stop()
                else:
                    avg_power, peak_power = 0.0, 0.0
                    
                throughput = iterations / 2.0 
                
            # Calculate Energy Efficiency (Only if we have power readings)
            gflops_per_watt = 0.0
            if tflops > 0 and avg_power > 0:
                tflops_per_sec = tflops * throughput
                gflops_per_watt = (tflops_per_sec * 1000) / avg_power
            
            # Update row data
            row.update({
                "Status": "Passed",
                "Latency_ms": round(avg_latency_ms, 2),
                "Throughput_passes_per_sec": round(throughput, 2),
                "Workload_TFLOPs": round(tflops, 4) if HAS_FLOP_COUNTER else "N/A",
                "Avg_Power_W": round(avg_power, 2) if avg_power > 0 else "N/A",
                "Peak_Power_W": round(peak_power, 2) if peak_power > 0 else "N/A",
                "Efficiency_GFLOPs_per_W": round(gflops_per_watt, 2) if gflops_per_watt > 0 else "N/A",
            })
            
            print("✅ PASSED")
            print(f"   Latency : {row['Latency_ms']} ms | Throughput : {row['Throughput_passes_per_sec']} passes/s")
            if device == "cuda":
                print(f"   Power   : {row['Avg_Power_W']} W (Avg) / {row['Peak_Power_W']} W (Peak)")
            if HAS_FLOP_COUNTER:
                print(f"   Compute : {row['Workload_TFLOPs']} TFLOPs", end="")
                if device == "cuda": print(f" | Efficiency: {row['Efficiency_GFLOPs_per_W']} GFLOPs/W")
                else: print()
            
        except Exception as e:
            error_msg = str(e).splitlines()[-1] if str(e) else "Unknown Error"
            print(f"❌ FAILED: {error_msg}")
            row["Error_Message"] = error_msg
            if device == "cuda":
                try: pynvml.nvmlShutdown() 
                except: pass
            
        csv_data.append(row)

    # --- CSV EXPORT ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hardware_profiling_{device}_{timestamp}.csv"
    
    print("\n" + "="*50)
    print("💾 EXPORTING RESULTS")
    print("="*50)
    
    fieldnames = csv_data[0].keys()
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
        
    print(f"✅ Data successfully saved to: {os.path.abspath(filename)}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TorchBench MIMD models on a specific hardware backend.")
    parser.add_argument(
        "-d", "--device", 
        type=str, 
        default="cuda", 
        help="Target hardware backend: 'cpu', 'cuda', 'mps' (Mac), 'xpu' (Intel), etc."
    )
    args = parser.parse_args()
    
    run_unified_stats(args.device)