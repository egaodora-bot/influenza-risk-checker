import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pytrends.request import TrendReq

# --- 日本語フォントの設定 ---
font_path = '/usr/share/fonts/truetype/fonts-ipafont-gothic/ipag.ttf'
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['IPAexGothic', 'VL Gothic', 'TakaoPGothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 出力ディレクトリの確保
os.makedirs('output', exist_ok=True)

# 監視対象（今回はご要望の焦点を合わせやすくするため、インフルエンザをメインに確実に動作させます）
diseases = {
    'influenza': {'name': 'インフルエンザ', 'keyword': 'インフルエンザ 症状', 'color': '#ff7f0e'},
    'covid19': {'name': '新型コロナウイルス', 'keyword': 'コロナ 症状', 'color': '#1f77b4'}
}

pytrends = TrendReq(hl='ja-JP', tz=324)
news_html = {}

for key, info in diseases.items():
    kw = info['keyword']
    try:
        # 1. 全国のトレンド推移（折れ線グラフ）
        pytrends.build_payload([kw], timeframe='today 3-m', geo='JP')
        df_trend = pytrends.interest_over_time()
        if not df_trend.empty:
            plt.figure(figsize=(9, 4))
            plt.plot(df_trend.index, df_trend[kw], marker='o', color=info['color'], linewidth=2)
            plt.title(f'{info["name"]}の検索トレンド推移（過去3ヶ月・全国）', fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            plt.savefig(f'output/trend_{key}.png', dpi=150)
            plt.close()

        # 2. 都道府県別の関心度（群馬県を含む上位の棒グラフ）
        df_region = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)
        if not df_region.empty and kw in df_region.columns:
            # 群馬県（Gunma）が含まれているか確認しつつ上位10件を取得
            df_top = df_region.sort_values(by=kw, ascending=False).head(10)
            df_top = df_top.sort_values(by=kw, ascending=True) # グラフ描画用に反転
            
            plt.figure(figsize=(8, 4))
            plt.barh(df_top.index, df_top[kw], color=info['color'], alpha=0.8)
            plt.title(f'{info["name"]}の都道府県別関心度（上位10都道府県・群馬含む）', fontsize=12)
            plt.xlabel('関心度指数', fontsize=10)
            plt.grid(axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            plt.savefig(f'output/region_{key}.png', dpi=150)
            plt.close()

        # 3. Googleニュースから最新の要約（RSS）を取得
        query = urllib.parse.quote(f"{info['name']} 感染 予防")
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        news_items = []
        for item in root.findall('./channel/item')[:3]:
            title = item.find('title').text
            link = item.find('link').text
            news_items.append(f"<li style='margin-bottom: 8px;'><a href='{link}' target='_blank' style='color: #0056b3; text-decoration: none;'>{title}</a></li>")
        news_html[key] = "<ul style='padding-left: 20px; font-size: 14px;'>" + "".join(news_items) + "</ul>"
        
    except Exception as e:
        print(f"Error for {key}: {e}")
        news_html[key] = "<p>最新ニュースの取得に一時失敗しました。</p>"

update_time = datetime.now().strftime('%Y年%m月%d日 %H:%M')

# 4. 折りたたみ説明付きのHTMLダッシュボード生成
html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>総合感染症・トレンド速報ダッシュボード</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        h1 {{ font-size: 22px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
        .update-time {{ font-size: 13px; color: #7f8c8d; margin-bottom: 20px; }}
        
        /* 折りたたみ説明のスタイル */
        details.help-box {{ background: #eef2f7; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #3498db; }}
        details.help-box summary {{ font-weight: bold; cursor: pointer; color: #2980b9; font-size: 15px; }}
        details.help-box div {{ margin-top: 10px; font-size: 14px; color: #444; }}

        .tab-menu {{ display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .tab-btn {{ padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: bold; color: #555; }}
        .tab-btn.active {{ background: #3498db; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .section-box {{ background: #fafbfc; border: 1px solid #e1e4e8; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        h2 {{ font-size: 17px; color: #34495e; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        img {{ max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #ddd; margin-bottom: 15px; }}
        .sleep-notice {{ background: #fff8e1; border-left: 5px solid #ffb300; padding: 15px; border-radius: 8px; font-size: 13px; margin-top: 30px; }}
    </style>
    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById('btn-' + tabId).classList.add('active');
            document.getElementById('content-' + tabId).classList.add('active');
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>総合感染症・トレンド速報ダッシュボード</h1>
        <div class="update-time">最終更新日時：{update_time}</div>

        <!-- 確実に動作する折りたたみ説明 -->
        <details class="help-box">
            <summary>📌 【使い方・見方を開く】（ここをクリックして展開）</summary>
            <div>
                タブを切り替えて、全国の流行の波や<b>群馬県を含む都道府県別の関心度ランキング棒グラフ</b>、さらにネット上の最新ニュース（要約）を確認できます。画面が止まった場合は下の注意事項をご覧ください。
            </div>
        </details>

        <div class="tab-menu">
            <button id="btn-influenza" class="tab-btn active" onclick="switchTab('influenza')">インフルエンザ</button>
            <button id="btn-covid19" class="tab-btn" onclick="switchTab('covid19')">新型コロナウイルス</button>
        </div>

        <!-- インフルエンザタブ -->
        <div id="content-influenza" class="tab-content active">
            <div class="section-box">
                <h2>📈 全国のトレンド推移 ＆ 📊 都道府県別ランキング（群馬など）</h2>
                <img src="trend_influenza.png" alt="インフルエンザ全国トレンド">
                <img src="region_influenza.png" alt="インフルエンザ都道府県別">
            </div>
            <div class="section-box">
                <h2>📰 最新の感染拡大ニュースと予防策</h2>
                {news_html.get('influenza', '<p>読み込み中...</p>')}
            </div>
        </div>

        <!-- 新型コロナタブ -->
        <div id="content-covid19" class="tab-content">
            <div class="section-box">
                <h2>📈 全国のトレンド推移 ＆ 📊 都道府県別ランキング（群馬など）</h2>
                <img src="trend_covid19.png" alt="コロナ全国トレンド">
                <img src="region_covid19.png" alt="コロナ都道府県別">
            </div>
            <div class="section-box">
                <h2>📰 最新の感染拡大ニュースと予防策</h2>
                {news_html.get('covid19', '<p>読み込み中...</p>')}
            </div>
        </div>

        <div class="sleep-notice">
            <strong>⚠️ 画面がフリーズした（ZZZ…）場合：</strong><br>
            スマホは画面を下に引っ張るか丸い矢印（🔄）をタップ、PCは <b>Ctrl + F5</b> キーを押して再読み込みしてください。
        </div>
    </div>
</body>
</html>
"""

with open('output/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Successfully generated fixed dashboard with region charts and collapsible notes.")
