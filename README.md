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

Python 3.13.1 の **Windows 11** 又は **Ubuntu 22.04 LTS** および汎用（リミックス）**Fedora 42** で、**NVIDIA RTX 3070 Super** と **A100** (CUDA 12.6) を搭載してテスト済みです。

### 1. コアの前提条件とグラフ作成ライブラリ
クリーンな Python 3.10 以降の環境があることを確認してください。 (`venv` または Conda 環境の使用を推奨します):
```bash
python3 -m pip install --upgrade pip setuptools wheel
pip install pandas pyyaml ninja psutil matplotlib seaborn
```
ウィンドウズでは、`pywin32` もインストールする必要かもしれません。

### 2. PyTorch とテレメトリのインストール
CUDA バージョンに合わせて最適化された PyTorch スタックとハードウェアテレメトリライブラリをインストールします:
```bash
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu126](https://download.pytorch.org/whl/cu126)
pip install nvidia-ml-py fvcore
```

### 3. TorchBench フレームワークのセットアップ
公式リポジトリをクローンし、MIMD に特化したワークロードをインストールします:
```bash
git clone [https://github.com/pytorch/benchmark](https://github.com/pytorch/benchmark)
cd benchmark
pip install -r requirements.txt
pip install -e .
python3 install.py --models dlrm soft_actor_critic bert_pytorch llama
```

> [!NOTE]
> これらのスクリプトには「スマートパスアンカー」機能が搭載されています。`torchbenchmark` フォルダ内から実行する必要はありません。スクリプトはベンチマークエンジンを自動検出するか、手動で指定することもできます。

---

## 🚀 自動化パイプライン

スイート全体を 3 つの簡単なステップで実行できます。

### ステップ 1: バッチスイープを実行する
テキストエディタ (`nano` や `vim` など) で `run_all.sh` を開きます。スクリプトが TorchBench ディレクトリ外にある場合は、コマンドラインで `--dir` 引数を設定してください。
```bash
$ python3 mimd-benchmark.py --dir /home/user/github/benchmark
```
スクリプトを実行可能にして実行すると、複数のバッチサイズにわたる自動 CPU および GPU テストが開始されます。
```bash
$ chmod +x run_all.sh
$ ./run_all.sh
```

### ステップ 2: データのマージ
スイープが完了したら、散在している CSV ファイルを統合します。
```bash
$ python3 merge_csvs.py
```
*出力: `master_benchmark_results.csv`*

### ステップ 3: 視覚化を生成する
生データを分析用のプロフェッショナルなチャートに変換します。
```bash
$ python3 generate_charts.py
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
> `$ python3 mimd-benchmark.py -d cuda -b 64 -t 120`
