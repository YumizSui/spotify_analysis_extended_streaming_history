"""メインエントリーポイント"""
import sys
from pathlib import Path
import pandas as pd
from src.loader import DataLoader
from src.analyzer import Analyzer
from src.reporter import Reporter


def main():
    """メイン処理"""
    print("=" * 60)
    print("Spotify Extended Streaming History Analyzer")
    print("=" * 60)

    try:
        # 1. Data Loader: データ読み込み
        print("\n[1/4] データ読み込み中...")
        loader = DataLoader()
        df = loader.load_all_audio_history()
        print(f"✓ {len(df):,} 件のレコードを読み込みました")

        # 2. Analyzer: 解析
        print("\n[2/4] データ解析中...")
        analyzer = Analyzer(df)

        kpis = analyzer.calculate_kpis()
        print(f"✓ KPI計算完了")

        # 基本機能
        top_artists_count = analyzer.get_top_artists_by_count(10)
        top_artists_duration = analyzer.get_top_artists_by_duration(10)
        top_tracks_count = analyzer.get_top_tracks_by_count(10)
        top_tracks_duration = analyzer.get_top_tracks_by_duration(10)
        top_albums_count = analyzer.get_top_albums_by_count(10)
        top_albums_duration = analyzer.get_top_albums_by_duration(10)
        peak_listening = analyzer.get_peak_listening_time()
        seasonal_trends = analyzer.get_seasonal_trends()
        listen_through_rate = analyzer.get_listen_through_rate_by_artist(20)

        print(f"✓ 基本解析完了")

        # 3. Reporter: グラフ生成
        print("\n[3/4] グラフ生成中...")
        reporter = Reporter()

        reporter.plot_top_artists(top_artists_count, "count", "top_artists_count.png")
        reporter.plot_top_artists(top_artists_duration, "duration", "top_artists_duration.png")
        reporter.plot_top_tracks(top_tracks_count, "count", "top_tracks_count.png")
        reporter.plot_top_tracks(top_tracks_duration, "duration", "top_tracks_duration.png")
        reporter.plot_peak_listening_time(peak_listening, "peak_listening_time.png")
        reporter.plot_seasonal_trends(seasonal_trends, "seasonal_trends.png")

        print(f"✓ グラフ生成完了")

        # 4. HTMLレポート生成
        print("\n[4/4] HTMLレポート生成中...")

        analysis_results = {
            "kpis": kpis,
            "top_artists_count": top_artists_count.to_dict("records"),
            "top_artists_duration": top_artists_duration.to_dict("records"),
            "top_tracks_count": top_tracks_count.to_dict("records"),
            "top_tracks_duration": top_tracks_duration.to_dict("records"),
        }

        reporter.generate_html_report(analysis_results)
        print(f"✓ HTMLレポート生成完了")

        print("\n" + "=" * 60)
        print("完了！ output/report.html を開いてください。")
        print("=" * 60)

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
