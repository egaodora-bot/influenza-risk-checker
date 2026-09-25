import os
import json
import datetime
import matplotlib.pyplot as plt

DATA_FILE = "data/history.json"

def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    today = datetime.date.today().isoformat()
    history = load_history()
    
    # ── [1] 最新データの取得（例としてダミーまたはAPI値を使用） ──
    # ※実際にはここで Google Trends や RSS から値を取得します
    current_value = 75  # 例：現在のトレンドスコア
    
    # 履歴に今日のデータがなければ追加
    if not any(item['date'] == today for item in history):
        history.append({"date": today, "value": current_value})
        # 過去30日分程度に絞る場合
        history = history[-30:]
        save_history(history)
    
    if len(history) < 2:
        print("データ蓄積中のため、分析をスキップします。")
        return

    # ── [2] 現状分析と未来予測（簡易ロジック） ──
    dates = [item['date'] for item in history]
    values = [item['value'] for item in history]
    
    recent_change = values[-1] - values[-5] if len(values) >= 5 else 0
    
    if recent_change > 10:
        outlook = "【警告】感染リスクの急ピッチな立ち上がりが見られます。今後2週間で注意報レベルに達する可能性があります。"
    elif recent_change > 0:
        outlook = "【注意】緩やかな増加傾向にあります。今後の推移に注意が必要です。"
    else:
        outlook = "【安定】現在のところ大きな変動はなく、落ち着いた推移をしています。"

    print("--- 感染症トレンド予測レポート ---")
    print(f"本日 ({today}) の状況: スコア {current_value}")
    print(f"展望予測: {outlook}")

    # ── [3] グラフの自動生成 ──
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='o', color='b', label='Historical Trend')
    plt.title("Infection Risk Trend & Forecast Monitor")
    plt.xlabel("Date")
    plt.ylabel("Index / Score")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    
    os.makedirs("output", exist_ok=True)
    plt.savefig("output/trend_chart.png")
    plt.close()
    print("グラフ画像を output/trend_chart.png に保存しました。")

if __name__ == "__main__":
    main()
