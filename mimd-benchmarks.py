import sys
import os
from pathlib import Path

def setup_paths(manual_path=None):
    """Finds the TorchBench root directory and anchors the script to it."""
    
    # --- MANUAL OVERRIDE ---
    if manual_path:
        target_dir = Path(manual_path).resolve()
        if (target_dir / "torchbenchmark").exists():
            root_str = str(target_dir)
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            os.chdir(root_str)
            print(f"🎯 Manually anchored to: {root_str}")
            return root_str
        else:
            print(f"❌ Error: Could not find 'torchbenchmark' inside the provided path:\n   {target_dir}")
            sys.exit(1)

    # --- AUTO-DISCOVERY FALLBACK ---
    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    potential_roots = [script_dir, cwd, script_dir.parent]
    
    found_root = None
    for path in potential_roots:
        if (path / "torchbenchmark").exists():
            found_root = path
            break
            
    if not found_root:
        print("❌ Error: Could not find the 'torchbenchmark' directory automatically.")
        print("Please use the --dir parameter to specify its location.")
        sys.exit(1)

    root_str = str(found_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    os.chdir(root_str)
    print(f"🏠 Auto-anchored to: {root_str}")
    return root_str

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

# Selected models that stress MIMD features (branching, sparse access, task parallelism)
MIMD_MODELS = [
    "dlrm",                 # Sparse + Dense hybrid (high memory-bandwidth & irregular access)
    "soft_actor_critic",    # RL: Irregular control flow and actor-critic logic
#    "drq",                  # RL: Data-regularized Q-learning
    "BERT_pytorch",         # NLP: Instruction-level branching in attention mechanisms
    "llama",                # LLM: Complex decoding logic and inference-heavy branching
#    "speech_transformer",   # Audio: Variable length sequences / complex dependencies
#    "tacotron2",            # Sequential/Recurrent dependencies
]

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


def run_unified_stats(device, batch_size=None, burn_duration=2.0):
    print(f"--- Running MIMD Suite on {device.upper()} ---")
    print(f"--- Burn Duration: {burn_duration}s | Batch Size: {batch_size or 'Default'} ---")
    
    csv_data = []

    for model_name in MIMD_MODELS:
        print(f"\n[ANALYZING]: {model_name}...", flush=True)
        
        # Define 'monitor' BEFORE the try block so it always exists, 
        # even if the model crashes immediately.
        monitor = None
        
        row = {
            "Model": model_name,
            "Backend": device,
            "Batch_Size": batch_size if batch_size else "Default",
            "Burn_Time_s": burn_duration,
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
            # 1. Initialize the TorchBench model
            module = importlib.import_module(f"torchbenchmark.models.{model_name}")
            kwargs = {"device": device, "test": "eval"}
            
            try:
                # Attempt to load with the custom batch size
                if batch_size is not None:
                    kwargs["batch_size"] = batch_size
                model_obj = module.Model(**kwargs)
                
            except Exception as init_err:
                # If TorchBench complains about the batch size, fall back to the default
                if batch_size is not None and "batch size" in str(init_err).lower():
                    print(f"\n   ⚠️ WARNING: {model_name} rejects custom batch sizes. Falling back to default.")
                    kwargs.pop("batch_size", None) # Remove the offending parameter
                    model_obj = module.Model(**kwargs)
                    
                    # Update the CSV row so you know this run didn't actually use the custom size
                    row["Batch_Size"] = "Default (Fallback)"
                else:
                    # If it failed for some other reason (like missing weights), raise the error normally
                    raise init_err
            
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
                # (Notice we removed 'monitor = None' from here!)
                if device == "cuda":
                    monitor = PowerMonitor()
                    monitor.start()
                
                start_time = time.time()
                iterations = 0
                while time.time() - start_time < burn_duration:
                    model_obj.invoke()
                    sync_device(device)
                    iterations += 1
                    
                if device == "cuda" and monitor:
                    avg_power, peak_power = monitor.stop()
                else:
                    avg_power, peak_power = 0.0, 0.0
                    
                throughput = iterations / float(burn_duration)
                
            # Calculate Energy Efficiency
            gflops_per_watt = 0.0
            if tflops > 0 and avg_power > 0:
                tflops_per_sec = tflops * throughput
                gflops_per_watt = (tflops_per_sec * 1000) / avg_power
            
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
            
            # --- THE CLEANUP FIX ---
            # If the model crashed mid-burn, gracefully kill the background thread
            if monitor:
                monitor.stop()
                
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
    parser.add_argument("-d", "--device", type=str, default="cuda", help="Target hardware backend: 'cpu', 'cuda', etc.")
    parser.add_argument("--dir", type=str, default=None, help="Manual path to the root benchmark directory (e.g., C:/github/benchmark)")
    
    parser.add_argument(
        "-b", "--batch-size", 
        type=int, 
        default=None, 
        help="Force a specific batch size. Increases computational density to saturate parallel compute units (SIMD lanes / MIMD threads)."
    )
    parser.add_argument(
        "-t", "--time", 
        type=float, 
        default=2.0, 
        help="Sustained burn duration in seconds. Longer times (e.g., 10-60s) capture steady-state power draw and trigger thermal throttling."
    )
    
    args = parser.parse_args()
    
    # Anchor the paths using the terminal argument (if provided) BEFORE running stats
    setup_paths(args.dir)
    
    run_unified_stats(args.device, args.batch_size, args.time)