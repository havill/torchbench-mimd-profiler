# MIMD ハードウェアプロファイリングスイート

ハードウェアに依存しない、完全に自動化されたプロファイリングパイプライン。異なるアーキテクチャ（CPU、CUDA、MPS など）上で PyTorch モデルを評価するために設計されています。**レイテンシ**、**スループット**、**ワークロード (テラフロップス)**、**エネルギー効率 (GFLOPS/ワット)** を測定し、比較用の可視化を自動的に生成します。

## 📂 リポジトリ構造

| ファイル | 説明 |
| :--- | :--- |
| `mimd-benchmark.py` | Python のコアプロファイリングエンジン。動的パスアンカー、フォールトトレランス、非同期電力テレメトリ機能を備えています。 |
| `run_all.sh` | CPU および GPU バックエンド全体でバッチサイズのスイープを自動化する Linux/macOS Bash スクリプト。 |
| `run_all.ps1` | ローカルテスト用の Windows PowerShell 相当のツールです。 |
| `merge_csvs.py` | 個々の実行出力を単一の `master_benchmark_results.csv` に統合するユーティリティです。 |
| `generate_charts.py` | マスター CSV を取り込み、Pandas/Seaborn を使用してプレゼンテーション用の PNG 棒グラフを生成します。 |

---

## 🛠️ 環境設定

Python 3.13.1 の **Windows 11** 又は **Ubuntu 22.04** および汎用（リミックス）**Fedora 42** で、**NVIDIA RTX 3070 Super** と **A100** (CUDA 12.6) を搭載してテスト済みです。

### 1. コアの前提条件とグラフ作成ライブラリ

クリーンな Python 3.10 以降の環境があることを確認してください。 (`venv` または Conda 環境の使用を推奨します):

```bash
python -m pip install --upgrade pip setuptools wheel
pip install pandas pyyaml ninja psutil matplotlib seaborn plotly  # generate_charts.pyの為
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
chmod +x run_all.sh
./run_all.sh
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
| `--time` | `-t` | Float | `2.0` | スループット/電力測定における持続バーン期間（秒）。 |
| `--dir` | ﾅｼ | 文字列 | *なし* | TorchBench リポジトリへのパスを手動で指定します。省略した場合は、パスアンカーによって自動検出されます。 |
| `--models` | ﾅｼ | リスト | デフォルトモデル群 | スペース区切りでモデル名を指定し、ベンチマーク対象をカスタマイズできます（例: `--models dlrm llama tts_angular`）。 |

**例:** バッチサイズ 64 で GPU に対して 60 秒間の高負荷サーマルスロットルテストを実行します。
`python mimd-benchmarks.py -d cuda -b 64 -t 60 --dir "/home/user/benchmark"`

## 🧠 ストレスパラメータの理解

ハードウェアを真に評価するには、単純な機能テストの域を超えなければなりません。このスイートは、アーキテクチャのストレステストに主に2つの要素を使用します。

* **バッチサイズ (`-b`): 計算負荷** これは、モデルが1回のフォワードパスで同時に処理する異なる入力の数を制御します。
* *重要な理由:* 標準的なモデルでは、バッチサイズが1で実行され、並列コアがアイドル状態になる場合があります。より大きなバッチサイズ (例: 32 または 64) を強制すると、チップの計算ユニットが飽和状態になります (GPU の SIMD レーンまたは MIMD チップの並列スレッドが埋まります)。より大きなバッチサイズを順に実行することで、ハードウェアがメモリ帯域幅の制約から計算の制約へと遷移する正確なポイントを把握するのに役立ちます。

* **時間 / 燃焼期間 (`-t`): 熱負荷**
これは、持続的な推論ループの実行時間 (秒単位) を正確に指定します。
* *重要理由:* デフォルトのTorchBenchテストは数ミリ秒で終了します。これは正確なワット数を測定したり、シリコンを加熱したりするには不十分な時間です。バーン時間を延長（例：10秒、30秒、または60秒）すると、ハードウェアを定常負荷状態に強制的に移行させ、正確な電力テレメトリを取得し、持続的な負荷下でチップがサーマルスロットリングの影響を受けていないかどうかを観察できます。

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

### `generate_charts.py` の新オプションと出力について

`generate_charts.py` は、マスターCSVから多彩なチャートを生成するツールです。最新版では以下のオプションと出力形式が利用できます：

#### コマンドラインオプション一覧

| オプション           | 説明                                                                                 |
|:-------------------- |:-----------------------------------------------------------------------------------|
| `-f, --file`         | 入力CSVファイルのパス（デフォルト: `000.combined-ALL.csv`）                          |
| `-m, --model`        | モデル名でチャートをフィルタリング（任意）                                           |
| `-b, --backend`      | バックエンド（CPU, CUDAなど）でチャートをフィルタリング（任意）                      |
| `-i, --interactive`  | Plotlyによるインタラクティブチャート（HTML形式）を生成                                |
| `-x, --export-formats` | 出力ファイル形式（例: `png,pdf,svg`。複数指定可。対応形式のみ保存）                |

#### 対応出力フォーマット

* PNG (`.png`)

* PDF (`.pdf`)
* SVG (`.svg`)
* JPEG (`.jpg`), EPS (`.eps`), TIFF (`.tiff`), WEBP (`.webp`) など
* インタラクティブHTML（`--interactive`指定時のみ）

※ GIFなど未対応形式を指定すると警告が表示され、対応形式のみ保存されます。

#### 生成されるチャート一覧

1. **スループット比較チャート**
    * バッチサイズ・モデル・バックエンドごとのスループット（Passes/sec）を棒グラフで表示
    * 各バーに数値ラベル（summary stats）付き
2. **エネルギー効率チャート（CUDAのみ）**
    * モデル・バッチサイズごとのGFLOPs/Wattを棒グラフで表示
    * 数値ラベル付き
3. **レイテンシ分布チャート**
    * バッチサイズ・バックエンドごとのレイテンシ（ms）を箱ひげ図で表示
    * 平均値アノテーション付き
4. **エラー率チャート**
    * モデル・バックエンドごとの失敗回数を棒グラフで表示
5. **インタラクティブチャート**
    * PlotlyによるHTML形式のスループットチャート（`--interactive`指定時）

---

##### 実行例

```bash
python generate_charts.py -f 000.combined-ALL.csv -m llama -b cuda -x png,pdf --interactive
```

この例では、llamaモデル・CUDAバックエンドのみを対象に、PNG/PDF形式のチャートとインタラクティブHTMLを生成します。

---

## ⚡ `--device` パラメータで指定できるデバイス一覧

`mimd-benchmarks.py` の `--device` パラメータはプロファイリング対象のハードウェアバックエンドを指定します。以下の値がサポートされています：

| デバイス | 説明                                                                                                   |
|:--------:|:------------------------------------------------------------------------------------------------------|
| cpu      | 標準CPUバックエンド（ホストプロセッサ上で実行。常に利用可能）                                           |
| cuda     | AMD ROCm (Radeon Open Compute) 又はNVIDIA CUDA (Compute Unified Device Architecture の略)              |
| mps      | Apple Siliconバックエンド（MacのM1/M2チップ用。PyTorchのMPSサポートが必要）                             |
| xpu      | Intel の「any Processing Unit」のoneAPIを利用（Intel製ディスクリートGPU用。PyTorchのXPUサポートが必要）   |
| hpu      | Habana Processing Unit（Intel Gaudi AIアクセラレータ用。PyTorchのHPUサポートが必要）                    |
| xla / openxla | XLAコンパイラ（Google TPUs用。Tensor Processing Unitにマッピング。PyTorch/XLAサポートが必要）      |
| meta     | メモリを割り当てずに形状・型・ニューラルネットワークグラフを追跡する「仮想」デバイス（デバッグ・解析用） |
