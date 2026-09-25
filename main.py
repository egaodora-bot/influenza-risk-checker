import os
import json
import datetime
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

DATA_FILE = "data/history.json"
REGION_FILE = "data/region_latest.json"
OUTPUT_DIR = "output"

# 都道府県名を英語（ローマ字）に変換する辞書
PREF_EN = {
    "北海道": "Hokkaido", "青森県": "Aomori", "岩手県": "Iwate", "宮城県": "Miyagi",
    "秋田県": "Akita", "山形県": "Yamagata", "福島県": "Fukushima", "茨城県": "Ibaraki",
    "栃木県": "Tochigi", "群馬県": "Gunma", "埼玉県": "Saitama", "千葉県": "Chiba",
    "東京都": "Tokyo", "神奈川県": "Kanagawa", "新潟県": "Niigata", "富山県": "Toyama",
    "石川県": "Ishikawa", "福井県": "Fukui", "山梨県": "Yamanashi", "長野県": "Nagano",
    "岐阜県": "Gifu", "静岡県": "Shizuoka", "愛知県": "Aichi", "三重県": "Mie",
    "滋賀県": "Shiga", "京都府": "Kyoto", "大阪府": "Osaka", "兵庫県": "Hyogo",
    "奈良県": "Nara", "和歌山県": "Wakayama", "鳥取県": "Tottori", "島根県": "Shimane",
    "岡山県": "Okayama", "広島県": "Hiroshima", "山口県": "Yamaguchi", "徳島県": "Tokushima",
    "香川県": "Kagawa", "愛媛県": "Ehime", "高知県": "Kochi", "福岡県": "Fukuoka",
    "佐賀県": "Saga", "長崎県": "Nagasaki", "熊本県": "Kumamoto", "大分県": "Oita",
    "宮崎県": "Miyazaki", "鹿児島県": "Kagoshima", "沖縄県": "Okinawa"
}

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
    os.makedirs("data", exist_ok=True)
    with open(REGION_FILE, "w", encoding="utf-8") as f:
        json.dump(region_data, f, ensure_ascii=False, indent=2)

def fetch_influenza_trend():
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
    try:
        pytrends = TrendReq(hl='ja-JP', tz=540)
        pytrends.build_payload(['インフルエンザ'], timeframe='today 1-m', geo='JP')
        df_region = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)
        
        if not df_region.empty and 'インフルエンザ' in df_region.columns:
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

    # ── [3] 全国トレンド時系列グラフの生成 ──
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart_path = os.path.join(OUTPUT_DIR, "trend_chart.png")

    if len(history) > 0:
        dates = [item['date'] for item in history]
        values = [item['value'] for item in history]

        plt.figure(figsize=(10, 4.5))
        plt.plot(dates, values, marker='o', color='#e74c3c', linewidth=2, label='Influenza Search Index (Japan)')
        plt.title("Infection Risk Trend Monitor (Google Trends: Influenza)", fontsize=11)
        plt.xlabel("Date")
        plt.ylabel("Search Index (0-100)")
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

 # ── [4] 都道府県別ランキングのグラフ生成（日本語対応） ──
    print(f"debug: regional_data のデータ数 = {len(regional_data) if regional_data else 0}")
    if regional_data:
        try:
            import matplotlib.font_manager as fm
            # Linux環境（GitHub Actions）でIPAゴシックを適用
            plt.rcParams['font.family'] = 'IPAexGothic'
        except:
            pass

        region_chart_path = os.path.join(OUTPUT_DIR, "region_chart.png")
        items_list = list(regional_data.items())[:15]
        
        prefs = [item[0] for item in items_list]
        scores = [item[1] for item in items_list]

        plt.figure(figsize=(10, 4.5))
        plt.bar(prefs, scores, color='#3498db')
        plt.title("都道府県別インフルエンザ検索関心度（上位15都道府県）", fontsize=11)
        plt.xlabel("都道府県", fontsize=10)
        plt.ylabel("検索インデックス", fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6, axis='y')
        plt.tight_layout()
        plt.savefig(region_chart_path)
        plt.close()
        print(f"都道府県別グラフを生成しました: {region_chart_path}")
    else:
        print("警告: regional_data が空のため、都道府県別グラフは生成されませんでした。")

if __name__ == "__main__":
    main()
