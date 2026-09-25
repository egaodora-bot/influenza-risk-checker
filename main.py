import os
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pytrends.request import TrendReq

DATA_FILE = "data/history.json"
REGION_HISTORY_FILE = "data/region_history.json"  # 変更: 都道府県データの履歴を蓄積するファイル
OUTPUT_DIR = "output"

def load_json(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default_val
                return json.loads(content)
        except json.JSONDecodeError:
            return default_val
    return default_val

def save_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
            today_str = datetime.date.today().isoformat()
            for pref, row in df_region.iterrows():
                regional_data[pref] = int(row['インフルエンザ'])
            return {"date": today_str, "data": regional_data}
    except Exception as e:
        print(f"都道府県別データ取得エラー: {e}")
    return None

def main():
    # ── [1] 全国時系列データの処理 ──
    history = load_json(DATA_FILE, [])
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

    save_json(DATA_FILE, history)

    # ── [2] 都道府県別データの履歴蓄積・管理 ──
    region_history = load_json(REGION_HISTORY_FILE, [])
    latest_region_entry = fetch_regional_trend()

    if latest_region_entry:
        # すでに今日のデータがあれば更新、なければ追加
        region_history = [item for item in region_history if item.get('date') != latest_region_entry['date']]
        region_history.append(latest_region_entry)
        # 直近14日分の履歴を保持
        region_history = sorted(region_history, key=lambda x: x['date'])[-14:]
        save_json(REGION_HISTORY_FILE, region_history)

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

    # ── [4] 都道府県別の「過去平均との比較（増加トレンド）」グラフ生成 ──
    print(f"debug: region_history の蓄積日数 = {len(region_history)}")
    if len(region_history) >= 2:
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

        current_data = region_history[-1]['data']
        # 過去のデータ（一番古いもの、または数日前の中央値など）を比較対象にする
        past_data = region_history[0]['data']

        diff_data = {}
        for pref, current_val in current_data.items():
            past_val = past_data.get(pref, current_val)
            # 過去数日間の平均や変化量を計算してスムーズにする
            diff_data[pref] = current_val - past_val

        # 増加量が大きい順にソート
        sorted_diff = sorted(diff_data.items(), key=lambda x: (x[1], current_data.get(x[0], 0)), reverse=True)
        items_list = sorted_diff[:15]
        
        prefs = [item[0] for item in items_list]
        diffs = [item[1] for item in items_list]

        region_chart_path = os.path.join(OUTPUT_DIR, "region_chart.png")
        plt.figure(figsize=(10, 4.5))
        
        colors = ['#e67e22' if d > 0 else '#3498db' for d in diffs]
        
        plt.bar(prefs, diffs, color=colors)
        plt.title("都道府県別インフルエンザ検索関心度の増加トレンド（過去からの変化・上位15都府県）", fontsize=11)
        plt.xlabel("都道府県", fontsize=10)
        plt.ylabel("過去からの増減ポイント", fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6, axis='y')
        plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
        plt.tight_layout()
        plt.savefig(region_chart_path)
        plt.close()
        print(f"都道府県別・増加トレンドグラフを生成しました: {region_chart_path}")
    else:
        print("情報: 比較するための過去データがまだ蓄積中のため、数日後に本格的なグラフが描画されます。")

if __name__ == "__main__":
    main()
