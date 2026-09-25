import os
import json
import datetime
import matplotlib.pyplot as plt

DATA_FILE = "data/history.json"
OUTPUT_DIR = "output"

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
    
    # ── [1] 最新データの取得（※ここではサンプルとして数値を使用しています） ──
    current_value = 75  # 将来的にここでGoogle Trendsや厚労省データを取得します
    
    # 本日のデータがまだ無ければ追加して保存
    if not any(item['date'] == today for item in history):
        history.append({"date": today, "value": current_value})
        history = history[-30:]  # 直近30日分を維持
        save_history(history)

    if len(history) == 0:
        return

    dates = [item['date'] for item in history]
    values = [item['value'] for item in history]

    # ── [2] グラフ画像の自動生成 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(OUTPUT_DIR, "trend_chart.png")

    plt.figure(figsize=(8, 4))
    plt.plot(dates, values, marker='o', color='#2980b9', linewidth=2)
    plt.title("Infection Risk Trend & Forecast Monitor", fontsize=12)
    plt.xlabel("Date")
    plt.ylabel("Risk Score")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    plt.savefig(chart_path)
    plt.close()
    print(f"グラフを生成しました: {chart_path}")

if __name__ == "__main__":
    main()
