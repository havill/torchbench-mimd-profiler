MIMD Hardware Profiling Suite for TorchBench
This suite provides a unified hardware profiling tool for evaluating PyTorch models on diverse backends (CPU, CUDA, MPS, etc.). It measures Latency, Throughput, Workload (TeraFLOPs), and Power Consumption (Watts), exporting the final results to a timestamped CSV.

🛠️ Environment Setup
Tested on:
- Windows 11 16GB RAM with an NVIDIA RTX 3070 Super
- Windows 11 64GB RAM with an NVIDIA RTX 4070 Super

1. Core Prerequisites
First, ensure you have a clean Python 3.10+ environment and the latest build tools:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install pywin32 pandas pyyaml ninja psutil
```
2. PyTorch Installation (CUDA 12.6+)
We used the CUDA 12.6 nightly/stable builds to ensure compatibility with modern hardware:

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```
3. TorchBench Framework
Clone the torchbenchmark repository, install the core requirements, and install the benchmark in editable mode:

```powershell
# From the root of the benchmark directory
pip install -r requirements.txt
pip install -e .
```
4. Model-Specific Dependencies
The script targets a specific "MIMD-friendly" subset of models. Install their individual requirements using the TorchBench internal installer:

```powershell
# Installs dependencies for the core suite
python install.py --models dlrm soft_actor_critic bert_pytorch llama

# Optional: Telemetry & Helper libraries
pip install nvidia-ml-py  # For GPU Power monitoring
pip install fvcore        # For FLOP counting
```

🚀 Running the Benchmarks
The script supports dynamic device selection via the -d flag.
- `-d cpu`: No special hardware libs used
- `-d cuda`: NVIDIA
- `-d mps`: Mac
- `-d xpu`: Intel

GPU Benchmarking (Full Telemetry)
Includes Power (Watts) and Energy Efficiency (GFLOPs/W) metrics:

```powershell
python mimd_benchmarks.py -d cuda
```
CPU Benchmarking
Runs the suite on the host processor (Power telemetry is automatically disabled):

```powershell
python mimd_benchmarks.py -d cpu
```

📊 Output
Upon completion, the script generates a timestamped CSV file:
hardware_profiling_[device]_[timestamp].csv

Tracked Metrics:
| Metric | Description |
| :--- | :--- |
| Latency | Average GPU/CPU time per forward pass (ms). |
| Throughput | Inferences per second (iter/sec). |
| Workload | Total mathematical operations in TeraFLOPs. |
| Avg Power | Sustained power draw in Watts (NVIDIA only). |
| Efficiency | Mathematical "Bang for your Buck" (GFLOPs per Watt). |

⚠️ Troubleshooting Notes
Tacotron2 / Speech Transformer: These models were excluded from the final suite due to complex Linux-specific dependencies (kaldiio, train_chars.txt) that are unstable on Windows.

AssertionErrors: If you see "unknown args" errors, ensure you are not passing unsupported flags like --flops or -b to the base run.py as these are now handled natively by the Python wrapper.
