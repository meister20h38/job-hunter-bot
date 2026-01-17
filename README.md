# JobHunter-Bot: 省電力・分散型AI就活エージェント
**「寝ている間に、GPUマシンが就活を終わらせる」**

就活サイト（Paiza）のスカウトを自動巡回し、ローカルLLMで解析・評価してDiscordに通知する分散型自動化システムです。
**省電力なLinuxサーバー**が指揮官となり、**高スペックなWindowsマシン**をWake-on-LAN (WOL) で必要な時だけ物理的に起動・操作する「グリーンITアーキテクチャ」を採用しています。

## Table of Contents
- [📸 Demo](#-demo)
- [🏗 Architecture](#-architecture)
- [🚀 Key Features](#-key-features)
- [🛠 Tech Stack](#-tech-stack)
- [🔥 Technical Challenges & Solutions](#-technical-challenges--solutions)
- [📦 Usage](#-usage)
- [📂 Project Structure](#-project-structure)

## 📸 Demo

実際にDiscordに基準以上の求人の通知を受信している様子です。
AIによるスコアを含む求人の情報がメリット・デメリットと共に表示されています。

![Demo App](./images/demo_discord.jpg)


## 🏗 Architecture

```mermaid

sequenceDiagram
    participant Ubuntu as 🐧 Ubuntu Server<br>(Commander)
    participant WinPC as 🪟 AI PC<br>(Worker)
    participant Paiza as 🌐 Paiza
    participant Discord as 🔔 Discord

    Note over Ubuntu: ⏰ AM 9:00 Cron発火
    Ubuntu->>WinPC: 🚀 Wake-on-LAN (Magic Packet)
    WinPC-->>WinPC: ⚡ 物理起動 (Boot)
    Ubuntu->>Ubuntu: ⏳ Ping監視 (起動待ち)   

Ubuntu->>WinPC: 🔑 SSH接続 (Script実行命令)
    
    rect rgb(240, 248, 255)
        Note over WinPC: 🤖 JobHunter-Bot 実行
        WinPC->>Paiza: 🕵️ Playwrightでログイン
        Paiza-->>WinPC: 最新スカウト取得
        WinPC->>WinPC: 🧠 Local LLM (Qwen2.5) で解析
        
        opt スコア >= 70
            WinPC->>Discord: 📨 通知送信
        end
    end

    Ubuntu->>WinPC: 💤 シャットダウン命令
    WinPC-->>WinPC: 🔌 電源OFF
    Note over Ubuntu: 🎉 ミッション完了

```

## 🚀 Key Features

* **Hybrid OS Orchestration**: Linux (Ubuntu) から Windows 11 をWOLとSSHを用いて完全にリモート制御。
* **Green IT Design**: 高消費電力なGPUマシンは、AI推論が必要な数分間のみ稼働。処理完了後は即座に自動シャットダウン。
* **Robust RPA Crawler**: APIではなくブラウザ操作 (Playwright) を採用し、動的なSPAサイトや複雑なログイン処理に対応。
* **Privacy First**: 求人票の解析にはローカルLLM (Ollama) を使用。個人の嗜好データや解析内容を外部に送信しません。

## 🛠 Tech Stack

* **Infrastructure**
  - **Commander**: Ubuntu Server 22.04 (Cron, Bash, Wake-on-LAN)
  - **Worker**: Windows 11 Pro (OpenSSH Server, Hyper-V Disabled)
  - **Hardware**: Ryzen 5 5950X / RTX 3060 (12GB) / Intel I211 NIC

* **Application**
  - **Language**: Python 3.10
  - **Automation**: Playwright (Browser Control)
  - **AI Runtime**: Ollama (Model: `qwen2.5:14b`)
  - **Notification**: Discord Webhook

## 🔥 Technical Challenges & Solutions

### 1. 外部からの物理マシン電源制御 (Wake-on-LAN)

- **🔴 課題**: 高性能な自作PC (Ryzen 5950X/RTX 3060) を使用しているが、マザーボードやOSの設定が複雑で、外部からのパケットで起動しない問題が発生。特にWindowsの「高速スタートアップ」がWOLを無効化してしまう仕様に苦戦した。

- **🟢 解決策**:
    - BIOS設定に加え、Intel NICドライバの "**PME (Power Management Event)**" を有効化。
    - Windowsのコントロールパネルから **「高速スタートアップ」を明示的に無効化** し、完全なシャットダウン状態からの復帰を実現。
    - Ubuntu側で `wakeonlan` 送信後に `ping` による死活監視ループを実装し、確実な起動を確認してからSSH接続するロジックを構築。

### 2. Gmail API から RPA への転換
- **🔴 課題**: 当初はGmail APIで通知メールを解析していたが、「既読メールが取得できない」「メール本文の情報量が少ない」「ラグがある」といった問題により、正確な求人解析が困難だった。

- **🟢 解決策**: アプローチを根本から変更し、**Playwright** によるブラウザ自動操作 (RPA) を採用。 サイトに直接ログインしてDOMを解析することで、リアルタイムかつ詳細な求人データの取得に成功。SPA特有の描画待ちには `networkidle` 待機ロジックを組み込み安定化させた。

### 3. SSH経由でのGUI/Encoding制御
- **🔴 課題**: SSH経由でPythonスクリプトを実行すると、WindowsのShift-JIS環境とLinuxのUTF-8環境の不整合でエラーが発生したり、GUIブラウザが起動できずに処理が停止した。

- **🟢 解決策**:
    - ブラウザを完全な **Headless Mode** で動作するように改修。
    - SSHコマンド発行時に `set PYTHONIOENCODING=utf-8` を注入し、絵文字（🤖など）を含むログ出力を正常化。

## 📦 Usage

1. Setup Windows (Worker)

```bash
# Clone Repository
git clone [https://github.com/meister20h38/job-hunter-bot.git](https://github.com/meister20h38/job-hunter-bot.git)
cd job-hunter-bot

# Install Dependencies
pip install -r requirements.txt
playwright install

# Configure Secrets
cp config.env.example config.env
# (Edit config.env with your settings)
```

2. Setup Ubuntu (Commander)

`scripts/daily_mission.sh` を配置し、Cronに登録します。

```bash
# Edit & Permission
chmod +x scripts/daily_mission.sh

# Setup Cron (Run at 9:00 AM)
crontab -e
# 0 9 * * * /path/to/job-hunter-bot/scripts/daily_mission.sh >> /path/to/mission.log 2>\&1
```

## 📂 Project Structure

```text
job-hunter-bot/
├── scripts/
│   └── daily_mission.sh   # Ubuntu用 指揮官スクリプト
├── src/
│   ├── main.py            # エントリーポイント
│   ├── paiza_crawler.py   # Playwright クローラー
│   ├── ai_client.py       # Ollama AI ロジック
│   └── ...
├── config.env.example     # 設定ファイルひな形
└── requirements.txt
```
