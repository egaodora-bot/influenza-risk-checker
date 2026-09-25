import feedparser
from pytrends.request import TrendReq
import datetime

# 1. 厚生労働省などのRSSから新着情報を取得する例
def check_mhlw_infuenza_rss():
    rss_url = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/kekkaku-kansensou/index.xml" # ※例のURL
    feed = feedparser.parse(rss_url)
    
    recent_news = []
    today = datetime.date.today()
    
    for entry in feed.entries:
        # 直近数日以内の発表をチェック
        # published_parsed などをパースして判定
        recent_news.append(entry.title)
        
    return recent_news

# 2. Google Trendsで「インフルエンザ」の検索意欲の立ち上がりを見る例
def check_google_trends():
    pytrends = TrendReq(hl='ja-JP', tz=324)
    kw_list = ["インフルエンザ"]
    pytrends.build_payload(kw_list, timeframe='today 1-m', geo='JP')
    data = pytrends.interest_over_time()
    
    if not data.empty:
        # 直近の検索ボリュームの傾き（トレンド）を計算
        recent_trend = data['インフルエンザ'].tail(7).mean()
        previous_trend = data['インフルエンザ'].head(7).mean()
        if recent_trend > previous_trend * 1.5:  
            return True, "検索数が急増しています（流行前の予兆の可能性）"
    return False, ""

if __name__ == "__main__":
    print("衛生・医療情報ソースの巡回を開始します...")
    # 実行処理
    trending, msg = check_google_trends()
    if trending:
        print(f"[警告] {msg}")