# MIMD ハードウェアプロファイリングスイート

ハードウェアに依存しない、完全に自動化されたプロファイリングパイプライン。異なるアーキテクチャ（CPU、CUDA、MPS など）上で PyTorch モデルを評価するために設計されています。**レイテンシ**、**スループット**、**ワークロード (テラフロップス)**、**エネルギー効率 (GFLOPS/ワット)** を測定し、比較用の可視化を自動的に生成します。

## 📂 リポジトリ構造

| ファイル | 説明 |
| :--- | :--- |
| `mimd-benchmark.py` | Python のコアプロファイリングエンジン。動的パスアンカー、フォールトトレランス、非同期電力テレメトリ機能を備えています。 |
| `run_all.sh` | CPU および GPU バックエンド全体でバッチサイズのスイープを自動化する Linux/macOS Bash スクリプト。 |
| `run_all.ps1` |ローカルテスト用の Windows PowerShell 相当のツールです。|
| `merge_csvs.py` | 個々の実行出力を単一の `master_benchmark_results.csv` に統合するユーティリティです。|
| `generate_charts.py` | マスター CSV を取り込み、Pandas/Seaborn を使用してプレゼンテーション用の PNG 棒グラフを生成します。|

---

## 🛠️ 環境設定

Python 3.13.1 の **Windows 11** 又は **Ubuntu 22.04** および汎用（リミックス）**Fedora 42** で、**NVIDIA RTX 3070 Super** と **A100** (CUDA 12.6) を搭載してテスト済みです。

### 1. コアの前提条件とグラフ作成ライブラリ
クリーンな Python 3.10 以降の環境があることを確認してください。 (`venv` または Conda 環境の使用を推奨します):
```bash
python -m pip install --upgrade pip setuptools wheel
pip install pandas pyyaml ninja psutil matplotlib seaborn
```
ウィンドウズでは、`pywin32` もインストールする必要があるかもしれません。

### 2. PyTorch とテレメトリのインストール
CUDA バージョンに合わせて最適化された PyTorch スタックとハードウェアテレメトリライブラリをインストールします:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install nvidia-ml-py fvcore
```

### 3. TorchBench フレームワークのセットアップ
公式リポジトリをクローンし、MIMD に特化したワークロードをインストールします:
```bash
git clone https://github.com/pytorch/benchmark
cd benchmark
pip install -r requirements.txt
pip install -e .
python install.py --models dlrm soft_actor_critic bert_pytorch llama
```

> [!NOTE]
> これらのスクリプトには「スマートパスアンカー」機能が搭載されています。`torchbenchmark` フォルダ内から実行する必要はありません。スクリプトはベンチマークエンジンを自動検出するか、手動で指定することもできます。

---

## 🚀 自動化パイプライン

スイート全体を 3 つの簡単なステップで実行できます。

### ステップ 1: バッチスイープを実行する
テキストエディタ (`nano` や `vim` など) で `run_all.sh` を開きます。スクリプトが TorchBench ディレクトリ外にある場合は、コマンドラインで `--dir` 引数を設定してください。
```bash
python mimd-benchmark.py --dir /home/user/github/benchmark
```
スクリプトを実行可能にして実行すると、複数のバッチサイズにわたる自動 CPU および GPU テストが開始されます。
```bash
$ chmod +x run_all.sh
$ ./run_all.sh
```

### ステップ 2: データのマージ
スイープが完了したら、散在している CSV ファイルを統合します。
```bash
python merge_csvs.py
```
*出力: `master_benchmark_results.csv`*

### ステップ 3: 視覚化を生成する
生データを分析用のプロフェッショナルなチャートに変換します。
```bash
python generate_charts.py
```
*出力: `chart_throughput_comparison.png` と `chart_energy_efficiency.png`*

---

## 📊 追跡対象メトリクス

* **レイテンシ (ms):** フォワードパスあたりの平均時間。
* **スループット (パス/秒):** 持続負荷下での推論速度の絶対値。
* **ワークロード (TFLOP):** モデルに必要な合計演算量。
* **電力 (ワット):** 持続およびピーク時の消費電力 (NVIDIA NVML が必要)。
* **効率 (GFLOP/W):** 消費電力あたりの計算収率。

---

> [!TIP]
> **ストレステストのカスタマイズ:** 自動化スクリプトをバイパスし、特定の負荷テストに対してコアプロファイラーを手動で実行できます。例 (CUDA、バッチサイズ 64、120 秒の書き込み):
> `python mimd-benchmark.py -d cuda -b 64 -t 120`

## 🎛️ コマンドラインリファレンス

### 1. コアプロファイラー (`mimd-benchmarks.py`)
これはメインエンジンです。非常に具体的な、単発の過酷なテストのために手動で実行できます。

| 引数 | ショート | 型 | デフォルト | 説明 |
| :--- | :---: | :--- | :--- | :--- |
| `--device` | `-d` | 文字列 | `cuda` | ターゲットハードウェアバックエンド (例: `cpu`、`cuda`、`mps`、`xpu`)。 |
| `--batch-size` | `-b` | Int | *なし* | 特定のバッチサイズを強制します。省略した場合は、モデルのデフォルトが使用されます。 |
| `--time` | `-t` | Float | `2.0` |スループット/電力測定における持続バーン期間（秒）。|
| `--dir` | ﾅｼ | 文字列 | *なし* | TorchBench リポジトリへのパスを手動で指定します。省略した場合は、パスアンカーによって自動検出されます。|

**例:** バッチサイズ 64 で GPU に対して 60 秒間の高負荷サーマルスロットルテストを実行します。
`python mimd-benchmarks.py -d cuda -b 64 -t 60 --dir "/home/user/benchmark"`

---

### 2. 自動化スイープ (`run_all.ps1` および `run_all.sh`)
これらのラッパースクリプトは、デバイスとバッチサイズ (1、8、16、32) のマトリックスにわたってコアプロファイラーを実行します。

**PowerShell (`run_all.ps1`)**
* `-Devices`: テストするデバイスのカンマ区切りリスト (デフォルト: `"cpu,cuda"`)。
* `-Dir`: TorchBench ディレクトリへのパスを手動で指定します。

**Bash (`run_all.sh`)**
* `-d`, `--device`: テストするデバイスのカンマ区切りリスト (デフォルト: `"cpu,cuda"`)。
* `--dir`: TorchBench ディレクトリへのパスを手動で指定します。

**例 (Windows):** `.\run_all.ps1 -Devices "cuda" -Dir "C:\benchmark"`
**例 (Linux):** `./run_all.sh -d "cpu,cuda" --dir "/home/user/benchmark"`

---

### 3. データマージャー (`merge_csvs.py`)
複数の実行CSVファイルを1つのマスターファイルに結合します。

| 引数 | ショート | 型 | デフォルト | 説明 |
| :--- | :---: | :--- | :--- | :--- |
| `--dir` | `-d` | 文字列 | `.` *(カレント)* | 結合するCSVファイルを含むディレクトリ。 |

**例:** 特定のハードウェアアーカイブフォルダ内のすべてのCSVをマージします。
`python merge_csvs.py --dir "./results_rtx3070"`

---

### 4. チャートジェネレーター (`generate_charts.py`)
マージされたマスターCSVを読み込み、高解像度のPNGチャートを出力します。

| 引数 | ショート | タイプ | デフォルト | 説明 |
| :--- | :---: | :--- | :--- | :--- |
| `--file` | `-f` | 文字列 | `master_benchmark_results.csv` | 可視化するマスターCSVファイルへの正確なパス。 |

**例:** 特定のアーカイブファイルからチャートを生成する:
`python generate_charts.py -f "./results_rtx3070/master_benchmark_results.csv"`
