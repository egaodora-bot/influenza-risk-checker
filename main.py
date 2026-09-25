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
    """Google Trendsから「インフルエンザ」の過去1ヶ月分の時系列データを取得する"""
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        # 過去1ヶ月間のデータを取得
        pytrends.build_payload(['インフルエンザ'], timeframe='today 1-m', geo='JP')
        df = pytrends.interest_over_time()
        
        if not df.empty and 'インフルエンザ' in df.columns:
            trend_data = []
            for date_val, row in df.iterrows():
                # Timestamp型を 'YYYY-MM-DD' 文字列に変換
                date_str = date_val.strftime('%Y-%m-%d')
                value = int(row['インフルエンザ'])
                trend_data.append({"date": date_str, "value": value})
            return trend_data
    except Exception as e:
        print(f"データ取得エラー: {e}")
    
    return None

def main():
    history = load_history()
    
    # ── [1] Google Trendsから過去1ヶ月分の時系列データを取得してマージ ──
    fetched_data = fetch_influenza_trend()
    
    if fetched_data:
        # 日付をキーにした辞書にして既存データと統合（重複を防ぐ）
        history_dict = {item['date']: item['value'] for item in history}
        for item in fetched_data:
            history_dict[item['date']] = item['value']
        
        # 日付順にソートしてリスト化し、直近60日分を保持
        sorted_dates = sorted(history_dict.keys())
        history = [{"date": d, "value": history_dict[d]} for d in sorted_dates]
        history = history[-60:]
        save_history(history)
    elif not history:
        # 取得できず履歴もない場合のフォールバック
        today = datetime.date.today().isoformat()
        history = [{"date": today, "value": 50}]

    if len(history) == 0:
        return

    dates = [item['date'] for item in history]
    values = [item['value'] for item in history]

    # ── [2] グラフ画像の自動生成 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(OUTPUT_DIR, "trend_chart.png")

    plt.figure(figsize=(10, 4.5))
    plt.plot(dates, values, marker='o', color='#e74c3c', linewidth=2, label='Influenza Search Index (Japan)')
    
    # 文字化け対策としてタイトルを英語表記に調整
    plt.title("Infection Risk Trend Monitor (Google Trends: Influenza)", fontsize=11)
    plt.xlabel("Date")
    plt.ylabel("Search Interest (0-100)")
    
    # X軸のラベルが多い場合に重ならないよう間引き・回転
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(chart_path)
    plt.close()
    print(f"時系列データに基づくグラフを生成しました: {chart_path} (データ数: {len(history)}件)")

if __name__ == "__main__":
    main()
