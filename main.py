"""メインエントリーポイント"""
import sys
from pathlib import Path
from datetime import datetime
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

        # 基本機能（最大100件取得してJSON用に保存）
        top_artists_count = analyzer.get_top_artists_by_count(100)
        top_artists_duration = analyzer.get_top_artists_by_duration(100)
        top_tracks_count = analyzer.get_top_tracks_by_count(100)
        top_tracks_duration = analyzer.get_top_tracks_by_duration(100)
        top_albums_count = analyzer.get_top_albums_by_count(100)
        top_albums_duration = analyzer.get_top_albums_by_duration(100)
        peak_listening = analyzer.get_peak_listening_time()
        seasonal_trends = analyzer.get_seasonal_trends()
        listen_through_rate = analyzer.get_listen_through_rate_by_artist(20)

        print(f"✓ 基本解析完了")

        # 年ごとの分析
        available_years = analyzer.get_available_years()
        yearly_kpis = analyzer.get_yearly_kpis()
        yearly_data = {}

        print(f"\n年ごとの解析中... ({len(available_years)}年分)")
        for year in available_years:
            yearly_data[year] = {
                "kpis": yearly_kpis[year],
                "top_artists_count": analyzer.get_top_artists_by_year(year, "count", 100),
                "top_artists_duration": analyzer.get_top_artists_by_year(year, "duration", 100),
                "top_tracks_count": analyzer.get_top_tracks_by_year(year, "count", 100),
                "top_tracks_duration": analyzer.get_top_tracks_by_year(year, "duration", 100),
                "top_albums_count": analyzer.get_top_albums_by_year(year, "count", 100),
                "top_albums_duration": analyzer.get_top_albums_by_year(year, "duration", 100),
                "peak_listening": analyzer.get_peak_listening_time_by_year(year),
            }
        print(f"✓ 年ごと解析完了")

        # 推移分析（JSON用に100件取得、表示は選択可能）
        print(f"\n推移分析中...")
        artist_trends = analyzer.get_artist_trends(top_n=100, cumulative=False)
        artist_trends_cumulative = analyzer.get_artist_trends(top_n=100, cumulative=True)
        # グラフ用には10件のみ
        artist_trends_for_plot = analyzer.get_artist_trends(top_n=10, cumulative=False)
        artist_trends_cumulative_for_plot = analyzer.get_artist_trends(top_n=10, cumulative=True)
        print(f"✓ アーティスト推移完了")

        # 3. Reporter: グラフ生成
        print("\n[3/4] グラフ生成中...")
        reporter = Reporter()

        # 推移グラフ（Plotly）- 初期表示用に10件のみ
        if not artist_trends_for_plot.empty:
            print("推移グラフ生成中...")
            reporter.plot_artist_trends_plotly(
                artist_trends_for_plot, "artist_trends.html", cumulative=False
            )
            reporter.plot_artist_trends_plotly(
                artist_trends_cumulative_for_plot, "artist_trends_cumulative.html", cumulative=True
            )

        print(f"✓ グラフ生成完了")

        # 3.5. JSONデータ生成
        print("\n[3.5/4] JSONデータ生成中...")

        # 全期間データのJSON生成（limitごとに分けずに全部のデータを保存）
        all_period_data = {
            "count": {
                "artists": reporter.save_top_artists_json(top_artists_count, "count"),
                "tracks": reporter.save_top_tracks_json(top_tracks_count, "count"),
                "albums": reporter.save_top_albums_json(top_albums_count, "count"),
            },
            "duration": {
                "artists": reporter.save_top_artists_json(top_artists_duration, "duration"),
                "tracks": reporter.save_top_tracks_json(top_tracks_duration, "duration"),
                "albums": reporter.save_top_albums_json(top_albums_duration, "duration"),
            }
        }

        reporter.save_data_json(all_period_data, "all_period_data.json")

        # 年ごとデータのJSON生成（limitごとに分けずに全部のデータを保存）
        yearly_data_json = {}
        for year in available_years:
            year_data = yearly_data[year]
            yearly_data_json[str(year)] = {
                "count": {
                    "artists": reporter.save_top_artists_json(year_data["top_artists_count"], "count"),
                    "tracks": reporter.save_top_tracks_json(year_data["top_tracks_count"], "count"),
                    "albums": reporter.save_top_albums_json(year_data["top_albums_count"], "count"),
                },
                "duration": {
                    "artists": reporter.save_top_artists_json(year_data["top_artists_duration"], "duration"),
                    "tracks": reporter.save_top_tracks_json(year_data["top_tracks_duration"], "duration"),
                    "albums": reporter.save_top_albums_json(year_data["top_albums_duration"], "duration"),
                }
            }

        reporter.save_data_json(yearly_data_json, "yearly_data.json")

        # アーティスト推移データのJSON生成（全件数分を保存）
        artist_trends_data = {
            "normal": reporter.save_artist_trends_json(artist_trends, cumulative=False),
            "cumulative": reporter.save_artist_trends_json(artist_trends_cumulative, cumulative=True)
        }
        reporter.save_data_json(artist_trends_data, "artist_trends_data.json")
        print(f"✓ JSONデータ生成完了")

        # 4. HTMLレポート生成
        print("\n[4/4] HTMLレポート生成中...")

        # 年ごとのデータを辞書形式に変換
        yearly_data_dict = {}
        for year in available_years:
            year_data = yearly_data[year]
            yearly_data_dict[year] = {
                "kpis": year_data["kpis"],
                "top_artists_count": year_data["top_artists_count"].to_dict("records"),
                "top_artists_duration": year_data["top_artists_duration"].to_dict("records"),
                "top_tracks_count": year_data["top_tracks_count"].to_dict("records"),
                "top_tracks_duration": year_data["top_tracks_duration"].to_dict("records"),
                "top_albums_count": year_data["top_albums_count"].to_dict("records"),
                "top_albums_duration": year_data["top_albums_duration"].to_dict("records"),
            }

        # 最終更新日を生成
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        analysis_results = {
            "kpis": kpis,
            "available_years": available_years,
            "yearly_data": yearly_data_dict,
            "top_artists_count": top_artists_count.to_dict("records"),
            "top_artists_duration": top_artists_duration.to_dict("records"),
            "top_tracks_count": top_tracks_count.to_dict("records"),
            "top_tracks_duration": top_tracks_duration.to_dict("records"),
            "top_albums_count": top_albums_count.to_dict("records"),
            "top_albums_duration": top_albums_duration.to_dict("records"),
            "has_artist_trends": not artist_trends.empty,
            "all_period_data_json": all_period_data,
            "yearly_data_json": yearly_data_json,
            "artist_trends_data_json": artist_trends_data,
            "last_updated": last_updated,
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
