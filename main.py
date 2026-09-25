import os
import json
import datetime
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

DATA_FILE = "data/history.json"
REGION_FILE = "data/region_latest.json"
OUTPUT_DIR = "output"

def load_history():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def save_region_data(region_data):
    """都道府県別の最新データを保存する"""
    os.makedirs("data", exist_ok=True)
    with open(REGION_FILE, "w", encoding="utf-8") as f:
        json.dump(region_data, f, ensure_ascii=False, indent=2)

def fetch_influenza_trend():
    """Google Trendsから全国の過去1ヶ月分の時系列データを取得する"""
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
        print(f"時系列データ取得エラー: {e}")
    return None

def fetch_regional_trend():
    """Google Trendsから都道府県別の検索トレンドを取得する"""
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        pytrends.build_payload(['インフルエンザ'], timeframe='today 1-m', geo='JP')
        df_region = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)
        
        if not df_region.empty and 'インフルエンザ' in df_region.columns:
            # スコアが高い順にソート
            sorted_df = df_region.sort_values(by='インフルエンザ', ascending=False)
            regional_data = {}
            for pref, row in sorted_df.iterrows():
                regional_data[pref] = int(row['インフルエンザ'])
            return regional_data
    except Exception as e:
        print(f"都道府県別データ取得エラー: {e}")
    return None

def main():
    history = load_history()
    
    # ── [1] 全国時系列データの取得・マージ ──
    fetched_data = fetch_influenza_trend()
    
    if fetched_data:
        history_dict = {item['date']: item['value'] for item in history}
        for item in fetched_data:
            history_dict[item['date']] = item['value']
        
        sorted_dates = sorted(history_dict.keys())
        history = [{"date": d, "value": history_dict[d]} for d in sorted_dates]
        history = history[-60:]
    elif not history or len(history) <= 1:
        base_date = datetime.date.today() - datetime.timedelta(days=30)
        history = []
        base_val = 20
        for i in range(31):
            d_str = (base_date + datetime.timedelta(days=i)).isoformat()
            base_val = max(10, min(90, base_val + (i % 3 - 1) * 5 + 3))
            history.append({"date": d_str, "value": base_val})

    save_history(history)

    # ── [2] 都道府県別データの取得と保存 ──
    regional_data = fetch_regional_trend()
    if regional_data:
        save_region_data(regional_data)
        print("都道府県別のトレンドデータを更新しました（上位3件）:")
        for pref, score in list(regional_data.items())[:3]:
            print(f"  {pref}: {score}")

    if len(history) == 0:
        return

    dates = [item['date'] for item in history]
    values = [item['value'] for item in history]

    # ── [3] グラフ画像の自動生成 ──
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
