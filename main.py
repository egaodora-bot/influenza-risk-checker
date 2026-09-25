import os
import json
import datetime
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

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

def fetch_influenza_trend():
    """Google Trendsから「インフルエンザ」の直近の検索トレンドを取得する"""
    try:
        # pytrendsの初期化（日本・JST指定）
        pytrends = TrendReq(hl='ja-JP', tz=540)
        # 取得したいキーワードと期間（直近1ヶ月間）
        pytrends.build_payload(['インフルエンザ'], timeframe='today 1-m', geo='JP')
        df = pytrends.interest_over_time()
        
        if not df.empty and 'インフルエンザ' in df.columns:
            # 最新の行の数値を取得
            latest_value = int(df['インフルエンザ'].iloc[-1])
            return latest_value
    except Exception as e:
        print(f"データ取得エラー（フォールバック値を使用します）: {e}")
    
    return None

def main():
    today = datetime.date.today().isoformat()
    history = load_history()
    
    # ── [1] 実データの取得（取得できない場合は直近の値かダミーを使用） ──
    current_value = fetch_influenza_trend()
    if current_value is None:
        # 万が一API制限などで取得できなかった前回の値、またはデフォルト値
        current_value = history[-1]['value'] if history else 50

    # 本日のデータがまだ無ければ追加して保存（同日の重複を防ぐ）
    history = [item for item in history if item['date'] != today]
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

    plt.figure(figsize=(9, 4.5))
    plt.plot(dates, values, marker='o', color='#e74c3c', linewidth=2, label='Influenza Search Index')
    plt.title("Infection Risk Trend Monitor (Google Trends: インフルエンザ)", fontsize=11)
    plt.xlabel("Date")
    plt.ylabel("Search Interest (0-100)")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(chart_path)
    plt.close()
    print(f"実データに基づくグラフを生成しました: {chart_path} (値: {current_value})")

if __name__ == "__main__":
    main()
