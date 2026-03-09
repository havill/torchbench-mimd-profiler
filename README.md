# MIMD Biased Hardware Profiling Suite

A fully automated, hardware-agnostic profiling pipeline designed to evaluate PyTorch models across different architectures (CPU, CUDA, MPS, etc.). It measures **Latency**, **Throughput**, **Workload (TeraFLOPs)**, and **Energy Efficiency (GFLOPs/Watt)**, and automatically generates comparative visualizations.

## 📂 Repository Structure

| File | Description |
| :--- | :--- |
| `mimd-benchmark.py` | The core Python profiling engine. Features dynamic path anchoring, fault tolerance, and async power telemetry. |
| `run_all.ps1` | Windows PowerShell script to automate batch size sweeps across CPU and GPU backends. |
| `run_all.sh` | Linux/macOS Bash equivalent for automated batch testing. |
| `merge_csvs.py` | Utility to consolidate individual run outputs into a single `master_benchmark_results.csv`. |
| `generate_charts.py` | Ingests the master CSV and generates presentation-ready PNG bar charts using Pandas/Seaborn. |

---

## 🛠️ Environment Setup

Tested on **Windows 11** with an **NVIDIA RTX 3070 Super** (CUDA 12.6).

### 1. Core Prerequisites & Graphing Libraries
Ensure you have a clean Python 3.10+ environment:
```powershell
python -m pip install --upgrade pip setuptools wheel
pip install pywin32 pandas pyyaml ninja psutil matplotlib seaborn
```
> [!NOTE]
> pywin32 not needed for Linux

### 2. PyTorch & Telemetry Installation
```powershell
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu126](https://download.pytorch.org/whl/cu126)
pip install nvidia-ml-py fvcore
```

### 3. TorchBench Framework Setup
Clone the official repository and install the specific MIMD-focused workloads:
```powershell
git clone [https://github.com/pytorch/benchmark](https://github.com/pytorch/benchmark)
cd benchmark
pip install -r requirements.txt
pip install -e .
python install.py --models dlrm soft_actor_critic bert_pytorch llama
```

> [!NOTE]
> The scripts feature a "Smart Path Anchor." You do not need to run them from inside the `torchbenchmark` folder. They will auto-discover the benchmark engine or can be pointed to it manually.

---

## 🚀 The Automated Pipeline

You can run the entire suite in three simple steps.

### Step 1: Execute the Batch Sweep
Open `run_all.ps1` (or `run_all.sh`) in a text editor. If your script is located outside the TorchBench directory, set the `$BENCHMARK_DIR` variable at the top of the file:
```powershell
$BENCHMARK_DIR = "C:\path\to\your\benchmark"
```
Run the script to begin the automated CPU and GPU tests across multiple batch sizes:
```powershell
PS > .\run_all.ps1
```

### Step 2: Merge the Data
Once the sweep is complete, consolidate the scattered CSV files:
```powershell
PS > python merge_csvs.py
```
*Output: `master_benchmark_results.csv`*

### Step 3: Generate Visualizations
Turn your raw data into professional charts for analysis:
```powershell
PS > python generate_charts.py
```
*Output: `chart_throughput_comparison.png` and `chart_energy_efficiency.png`*

---

## 📊 Tracked Metrics

* **Latency (ms):** Average time per forward pass.
* **Throughput (passes/sec):** Absolute inference speed under sustained load.
* **Workload (TFLOPs):** Total mathematical operations required by the model.
* **Power (Watts):** Sustained and peak power draw (NVIDIA NVML required).
* **Efficiency (GFLOPs/W):** Computational yield per unit of power consumed.

---

> [!TIP]
> **Customizing Stress Tests:** You can bypass the automation scripts and run the core profiler manually for specific torture tests. Example (CUDA, Batch Size 64, 120-second burn):
> `python mimd-benchmark.py -d cuda -b 64 -t 120`
