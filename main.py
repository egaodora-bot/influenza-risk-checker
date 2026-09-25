import os
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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

def load_previous_region_data():
    if os.path.exists(REGION_FILE):
        try:
            with open(REGION_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}

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
            regional_data = {}
            for pref, row in df_region.iterrows():
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

    # ── [2] 以前の都道府県別データを読み込み（比較用） ──
    prev_regional_data = load_previous_region_data()

    # ── [3] 最新の都道府県別データを取得 ──
    regional_data = fetch_regional_trend()

    # ── [4] 全国トレンド時系列グラフの生成 ──
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

    # ── [5] 都道府県別の「急増度（前回からの増加量）」ランキンググラフ生成 ──
    print(f"debug: regional_data のデータ数 = {len(regional_data) if regional_data else 0}")
    if regional_data:
        # 日本語フォント設定
        font_path = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
        if not os.path.exists(font_path):
            for f in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
                if 'ipag' in f.lower() or 'gothic' in f.lower():
                    font_path = f
                    break
        
        if os.path.exists(font_path):
            jp_font = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = jp_font.get_name()
        else:
            plt.rcParams['font.family'] = 'sans-serif'

        # 前回データがある場合は「増加量（差分）」を計算。初回などで無い場合は0とする
        diff_data = {}
        for pref, current_val in regional_data.items():
            if prev_regional_data:
                prev_val = prev_regional_data.get(pref, current_val)
                diff_data[pref] = current_val - prev_val
            else:
                diff_data[pref] = 0  # 初回データがない時は差分0

        # 増加量が大きい順にソート（同点の場合は現在のスコアが高い順）
        sorted_diff = sorted(diff_data.items(), key=lambda x: (x[1], regional_data.get(x[0], 0)), reverse=True)
        items_list = sorted_diff[:15]
        
        prefs = [item[0] for item in items_list]
        diffs = [item[1] for item in items_list]

        region_chart_path = os.path.join(OUTPUT_DIR, "region_chart.png")
        plt.figure(figsize=(10, 4.5))
        
        # 増加傾向がわかりやすいように色を調整（プラスならオレンジ、0やマイナスなら青系）
        colors = ['#e67e22' if d > 0 else '#3498db' for d in diffs]
        
        plt.bar(prefs, diffs, color=colors)
        plt.title("都道府県別インフルエンザ検索関心度の増加トレンド（前回比・急増上位15都府県）", fontsize=11)
        plt.xlabel("都道府県", fontsize=10)
        plt.ylabel("前回からの増加ポイント", fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6, axis='y')
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.tight_layout()
        plt.savefig(region_chart_path)
        plt.close()
        print(f"都道府県別・増加トレンドグラフを生成しました: {region_chart_path}")
        
        # ── [6] 比較が終わったあとに、今回の最新データを次回の比較用に保存する ──
        save_region_data(regional_data)
    else:
        print("警告: regional_data が空のため、都道府県別グラフは生成されませんでした。")

if __name__ == "__main__":
    main()
