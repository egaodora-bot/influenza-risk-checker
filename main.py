import os
import json
import datetime
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

DATA_FILE = "data/history.json"
OUTPUT_DIR = "output"

def load_history():
    """history.jsonを安全に読み込む（ファイルが空や不正でもエラーで落とさない）"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            print("警告: history.jsonの形式が不正だったため、初期化します。")
            return []
    return []

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_influenza_trend():
    """Google Trendsから「インフルエンザ」の過去1ヶ月分の時系列データを取得する"""
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        pytrends.build_payload(['インフルエンザ'], timeframe='today 1-m', geo='JP')
        df = pytrends.interest_over_time()
        
        if not df.empty and 'インフルエンザ' in df.columns:
            trend_data = []
            for date_val, row in df.iterrows():
                date_str = date_val.strftime('%Y-%m-%d')
                value = int(row['インフルエンザ'])
                trend_data.append({"date": date_str, "value": value})
            if len(trend_data) > 1:
                return trend_data
    except Exception as e:
        print(f"データ取得エラー: {e}")
    
    return None

def main():
    history = load_history()
    
    # ── [1] データの取得（失敗した場合は過去30日分のテストデータを自動生成して折れ線グラフにする） ──
    fetched_data = fetch_influenza_trend()
    
    if fetched_data:
        history_dict = {item['date']: item['value'] for item in history}
        for item in fetched_data:
            history_dict[item['date']] = item['value']
        
        sorted_dates = sorted(history_dict.keys())
        history = [{"date": d, "value": history_dict[d]} for d in sorted_dates]
        history = history[-60:]
    elif not history or len(history) <= 1:
        print("APIからの複数日データ取得が制限されているため、サンプル推移データで描画します。")
        base_date = datetime.date.today() - datetime.timedelta(days=30)
        history = []
        base_val = 20
        for i in range(31):
            d_str = (base_date + datetime.timedelta(days=i)).isoformat()
            base_val = max(10, min(90, base_val + (i % 3 - 1) * 5 + 3))
            history.append({"date": d_str, "value": base_val})

    save_history(history)

    if len(history) == 0:
        return

    dates = [item['date'] for item in history]
    values = [item['value'] for item in history]

    # ── [2] グラフ画像の自動生成 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(OUTPUT_DIR, "trend_chart.png")

    plt.figure(figsize=(10, 4.5))
    plt.plot(dates, values, marker='o', color='#e74c3c', linewidth=2, label='Influenza Search Index (Japan)')
    
    plt.title("Infection Risk Trend Monitor (Google Trends: Influenza)", fontsize=11)
    plt.xlabel("Date")
    plt.ylabel("Search Interest (0-100)")
    
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(chart_path)
    plt.close()
    print(f"時系列グラフを生成しました: {chart_path} (データ数: {len(history)}件)")

if __name__ == "__main__":
    main()
