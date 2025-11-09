RPLIDAR A1 → OSC（Python） → 可視化（Processing）

RPLIDAR A1 を Python で読み取り、OSC で配信。Processing 側で受信・可視化します。
UDP/OSC を 3 分割送信してバッファあふれを回避する構成です。

動作確認環境

macOS 10.15.7（Intel）

RPLIDAR A1（USB ドングル）

Python 3.9（仮想環境）

Processing 4.x + oscP5 ライブラリ

注：Apple Silicon / 新しい macOS でも基本同様です。ドライバ（CH340/CP210x）が必要な場合があります。

1. ファイル構成
rplidar-osc/
├─ sender/                      # 送信（Python）
│  ├─ rplidar_osc.py
│  └─ requirements.txt
└─ receiver/                    # 受信（Processing）
   └─ RPLidarOscViewer.pde

2. 準備（共通）
2.1 Homebrew（未導入なら）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# インテルMac例（必要なら）
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
brew --version

2.2 Python（任意）

macOS の python3 でOK。Homebrew で入れ直す場合は brew install python。

2.3 仮想環境（推奨）
# リポジトリを任意の場所へ展開した想定
cd rplidar-osc/sender

python3 -m venv .venv
source .venv/bin/activate

# 依存導入
pip install --upgrade pip
pip install -r requirements.txt


requirements.txt（同梱）：

rplidar
python-osc
pyserial

3. RPLIDAR の接続

付属USBドングルに A1 を接続（USB と 5V 給電）。

モータが回転すれば通電OK。

デバイス名を確認：

ls /dev/tty.usb* /dev/cu.usb* 2>/dev/null
# 例: /dev/tty.usbserial-0001


何も出ない場合は USB-シリアルドライバ（CH340/CP210x）を導入してください。

4. 送信（Python / OSC）

sender/rplidar_osc.py（同梱）の実行方法：

cd rplidar-osc/sender
source .venv/bin/activate
python rplidar_osc.py /dev/tty.usbserial-0001 8000


第1引数：RPLIDAR のシリアルポート（環境に合わせて）

第2引数：OSC送信ポート（デフォルト 8000）

4.1 スクリプトのポイント（すでに反映済み）

RPLidar(serial, baudrate=115200, timeout=3) の正しい引数順

/rplidar/scan を 120本×3分割で送信（[start, d0..d119] 形式）

5. 受信・可視化（Processing）
5.1 ライブラリ導入

Processing を起動 → Sketch > Import Library > Add Library… → oscP5 をインストール。

5.2 スケッチ実行

receiver/RPLidarOscViewer.pde を開いて実行。
デフォルトで ポート 8000 をリッスンします。

受信データ：

旧仕様互換：/rplidar/scan に float[360]（未使用でも受信可）

分割仕様：/rplidar/scan に [start, d0..d119] で 3 回/フレーム

表示操作：[/] スケール、{/} 最大距離、</> 最小距離

6. まずは動作確認

Python 送信を先に起動

cd rplidar-osc/sender
source .venv/bin/activate
python rplidar_osc.py /dev/tty.usbserial-0001 8000
# Connected などが表示される


Processing 受信を起動
点群が出ればOK。

7. トラブルシューティング
7.1 Python 側で接続エラー

ポート名ミス：ls /dev/tty.usb* /dev/cu.usb* で再確認

ドライバ未導入：CH340/CP210x を導入

他アプリが掴んでいる：他のターミナルやツールを終了

7.2 ValueError: invalid literal for int() with base 10: '/dev/tty...'

RPLidar(None, serial, ...) の誤用。必ず RPLidar(serial, baudrate=115200, timeout=3) に。

7.3 Processing コンソールに

ArrayIndexOutOfBoundsException / UdpServer.run()

1パケットが大きすぎ。**分割送信（本READMEの構成）**を使う。

OscProperties#setDatagramSize(4096) で緩和できる場合もありますが、UDP安定性の観点から分割推奨。

7.4 InvocationTargetException / oscEvent

型/長さの想定がズレたときに発生。受信コードはtypetagで型吸収するようになっています（同梱版OK）。

デバッグ用に：

println("[OSC] addr=", m.addrPattern(), "typetag=", m.typetag(), "argc=", (m.arguments()!=null?m.arguments().length:-1));

7.5 距離が0のまま / 点が出ない

近すぎ/遠すぎ：minDist / maxDist を調整

回転していない：配線・給電確認（モータ回転/LED）

8. 送信フォーマット仕様

アドレス：/rplidar/scan

3回/フレーム送信（各120本）

引数：[start, d0, d1, ... d119]

start：0 / 120 / 240 のいずれか（開始インデックス、度単位）

dN：距離（mm、float推奨／intでも可）

受信側は start に基づいて scan[start + i] = d[i] として 360 本を復元。

9. 拡張アイデア

軽量化：mm → cm×10 の int16 化、Blob送信

フィルタ：移動平均/中央値でチラつき低減

機能：セクタごとの最小距離 /rplidar/min/{left,center,right}、閾値内侵入時 /rplidar/hit など

他アプリ：Max/MSP、TouchDesigner、Unity、openFrameworks 受信サンプル

10. ライセンス・出典

Python ライブラリ：rplidar（Roboticia）/ python-osc / pyserial

Processing ライブラリ：oscP5