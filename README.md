# MIMD vs. SIMD Hardware Profiling Suite

A fully automated, hardware-agnostic profiling pipeline designed to evaluate PyTorch models across different architectures (CPU, CUDA, MPS, etc.). It measures **Latency**, **Throughput**, **Workload (TeraFLOPs)**, and **Energy Efficiency (GFLOPs/Watt)**, and automatically generates comparative visualizations.

## 📂 Repository Structure

| File | Description |
| :--- | :--- |
| `mimd-benchmark.py` | The core Python profiling engine. Features dynamic path anchoring, fault tolerance, and async power telemetry. |
| `run_all.sh` | Linux/macOS Bash script to automate batch size sweeps across CPU and GPU backends. |
| `run_all.ps1` | Windows PowerShell equivalent for local testing. |
| `merge_csvs.py` | Utility to consolidate individual run outputs into a single `master_benchmark_results.csv`. |
| `generate_charts.py` | Ingests the master CSV and generates presentation-ready PNG bar charts using Pandas/Seaborn. |

---

## 🛠️ Environment Setup

Tested on **Ubuntu 22.04 LTS** and generic (remix) **Fedora 42** with an **NVIDIA RTX 3070 Super** and a **A100** (CUDA 12.6).

### 1. Core Prerequisites & Graphing Libraries
Ensure you have a clean Python 3.10+ environment. (We recommend using a `venv` or Conda environment):
```bash
python3 -m pip install --upgrade pip setuptools wheel
pip install pandas pyyaml ninja psutil matplotlib seaborn
```

### 2. PyTorch & Telemetry Installation
Install the PyTorch stack optimized for your CUDA version, along with the hardware telemetry libraries:
```bash
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu126](https://download.pytorch.org/whl/cu126)
pip install nvidia-ml-py fvcore
```

### 3. TorchBench Framework Setup
Clone the official repository and install the specific MIMD-focused workloads:
```bash
git clone [https://github.com/pytorch/benchmark](https://github.com/pytorch/benchmark)
cd benchmark
pip install -r requirements.txt
pip install -e .
python3 install.py --models dlrm soft_actor_critic bert_pytorch llama
```

> [!NOTE]
> The scripts feature a "Smart Path Anchor." You do not need to run them from inside the `torchbenchmark` folder. They will auto-discover the benchmark engine or can be pointed to it manually.

---

## 🚀 The Automated Pipeline

You can run the entire suite in three simple steps.

### Step 1: Execute the Batch Sweep
Open `run_all.sh` in a text editor (like `nano` or `vim`). If your script is located outside the TorchBench directory, set the `--dir` argument at the command line:
```bash
$ python mimd-benchmark.py --dir /home/user/github/benchmark
```
Make the script executable and run it to begin the automated CPU and GPU tests across multiple batch sizes:
```bash
$ chmod +x run_all.sh$ ./run_all.sh
```

### Step 2: Merge the Data
Once the sweep is complete, consolidate the scattered CSV files:
```bash
$ python3 merge_csvs.py
```
*Output: `master_benchmark_results.csv`*

### Step 3: Generate Visualizations
Turn your raw data into professional charts for analysis:
```bash
$ python3 generate_charts.py
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
> `$ python3 mimd-benchmark.py -d cuda -b 64 -t 120`
