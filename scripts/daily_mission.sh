#!/bin/bash

# 設定ファイルの読み込み
# スクリプトの1つ上の階層にある config.env を探す
CONFIG_FILE="$(dirname "$0")/../config.env"

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "❌ Error: config.env が見つかりません。"
    echo "config.env.example をコピーして作成してください。"
    exit 1
fi

echo "🌅 [$(date)] ミッション開始: AI PC起動シーケンス"

# 1. WOL発射
echo "🚀 Magic Packet 送信... ($TARGET_MAC)"
# ネットワーク環境に合わせてブロードキャストアドレス(-i)を調整してください
wakeonlan -i 192.168.50.255 $TARGET_MAC

# 2. 起動待ち
echo "⏳ 起動待機中... ($TARGET_IP)"
MAX_RETRIES=40
COUNT=0

while ! ping -c 1 -W 1 $TARGET_IP > /dev/null; do
    echo "   ...応答なし ($COUNT/$MAX_RETRIES)"
    sleep 5
    ((COUNT++))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ タイムアウト: AI PCが起動しませんでした。"
        exit 1
    fi
done

echo "✅ AI PCの起動を確認！ SSH接続待機中..."
sleep 20 

# 3. リモート実行
echo "🤖 JobHunter-Bot を実行します..."
# 環境変数でパスを受け渡して実行
ssh -o ConnectTimeout=10 $TARGET_USER@$TARGET_IP "cd $WORK_DIR_PATH && set PYTHONIOENCODING=utf-8 && $PYTHON_EXE_PATH $SCRIPT_NAME"

JOB_STATUS=$?

if [ $JOB_STATUS -eq 0 ]; then
    echo "🎉 ジョブ正常終了。"
else
    echo "⚠️ ジョブがエラーで終了しました (Code: $JOB_STATUS)"
fi

# 4. シャットダウン
echo "💤 AI PCをシャットダウンします..."
ssh $TARGET_USER@$TARGET_IP "shutdown /s /t 10"

echo "✅ [$(date)] 全ミッション完了。"
