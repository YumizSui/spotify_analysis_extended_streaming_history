"""Reporter: グラフ生成とHTMLレポート生成"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # バックエンドを明示的に設定
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, List, Optional
import requests
from jinja2 import Template
import json
import numpy as np
import japanize_matplotlib  # スタイル設定の後にインポート


class Reporter:
    """グラフ生成とHTMLレポート生成"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.assets_dir = self.output_dir / "assets"
        self.data_dir = self.output_dir / "data"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # スタイル設定
        plt.style.use("seaborn-v0_8-darkgrid")
        sns.set_palette("husl")

        # スタイル設定後に日本語フォントを再設定
        japanize_matplotlib.japanize()  # 明示的に呼び出し

        # 韓国語・中国語対応のため、CJK対応フォントを設定
        import matplotlib.font_manager as fm
        import platform

        # macOSの場合、AppleGothicやHiragino Sansを使用
        if platform.system() == 'Darwin':  # macOS
            # AppleGothicは韓国語・中国語・日本語に対応
            plt.rcParams['font.family'] = ['AppleGothic', 'Hiragino Sans', 'Arial Unicode MS', 'sans-serif']
        else:
            # その他のOSではNoto Sans CJKなどを探す
            font_list = fm.findSystemFonts()
            cjk_fonts = []
            for font_path in font_list:
                try:
                    font_prop = fm.FontProperties(fname=font_path)
                    font_name = font_prop.get_name()
                    if any(keyword in font_name.lower() for keyword in ['noto', 'nanum', 'malgun']):
                        cjk_fonts.append(font_name)
                except:
                    pass

            if cjk_fonts:
                plt.rcParams['font.family'] = cjk_fonts[0]

        # フォント警告を抑制（一部の文字が表示されない場合でも続行）
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')

    def download_album_art(self, url: str, track_id: str) -> Optional[str]:
        """アルバムアートをダウンロードして保存"""
        if not url:
            return None

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                file_path = self.assets_dir / f"{track_id}.jpg"
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return f"assets/{track_id}.jpg"
        except Exception as e:
            print(f"アルバムアートダウンロードエラー: {e}")

        return None

    def plot_artist_trends_plotly(self, trends_df: pd.DataFrame, output_name: str, cumulative: bool = False):
        """アーティストごとの再生推移（Plotly）"""
        if trends_df.empty:
            return

        fig = go.Figure()

        artists = trends_df["artist"].unique()
        colors = px.colors.qualitative.Set3

        for i, artist in enumerate(artists):
            artist_data = trends_df[trends_df["artist"] == artist].sort_values("date")

            if cumulative:
                y_col = "cumulative_hours"
                y_label = "累積再生時間 (時間)"
            else:
                y_col = "total_hours"
                y_label = "再生時間 (時間)"

            fig.add_trace(go.Scatter(
                x=artist_data["date"],
                y=artist_data[y_col],
                mode="lines+markers",
                name=artist,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6)
            ))

        fig.update_layout(
            title="アーティストごとの再生推移",
            xaxis_title="日付",
            yaxis_title=y_label,
            hovermode="x unified",
            height=600,
            font=dict(size=12)
        )

        fig.write_html(str(self.images_dir / output_name))

    def save_top_artists_json(self, top_artists: pd.DataFrame, metric: str, limit: int = None) -> Dict:
        """トップアーティストデータをJSON形式で返す"""
        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_artists_sorted = top_artists.sort_values(y_col, ascending=False)
        if limit is not None:
            top_artists_sorted = top_artists_sorted.head(limit)

        return {
            "metric": metric,
            "ylabel": ylabel,
            "data": top_artists_sorted.to_dict("records")
        }

    def save_top_tracks_json(self, top_tracks: pd.DataFrame, metric: str, limit: int = None) -> Dict:
        """トップトラックデータをJSON形式で返す"""
        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_tracks_sorted = top_tracks.sort_values(y_col, ascending=False)
        if limit is not None:
            top_tracks_sorted = top_tracks_sorted.head(limit)

        return {
            "metric": metric,
            "ylabel": ylabel,
            "data": top_tracks_sorted.to_dict("records")
        }

    def save_top_albums_json(self, top_albums: pd.DataFrame, metric: str, limit: int = None) -> Dict:
        """トップアルバムデータをJSON形式で返す"""
        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_albums_sorted = top_albums.sort_values(y_col, ascending=False)
        if limit is not None:
            top_albums_sorted = top_albums_sorted.head(limit)

        return {
            "metric": metric,
            "ylabel": ylabel,
            "data": top_albums_sorted.to_dict("records")
        }

    def save_artist_trends_json(self, trends_df: pd.DataFrame, cumulative: bool = False) -> Dict:
        """アーティスト推移データをJSON形式で返す"""
        if trends_df.empty:
            return {
                "cumulative": cumulative,
                "data": []
            }

        # DataFrameを辞書形式に変換
        trends_dict = trends_df.to_dict("records")

        # 日付を文字列に変換
        for record in trends_dict:
            if "date" in record and pd.notna(record["date"]):
                record["date"] = record["date"].strftime("%Y-%m-%d")

        return {
            "cumulative": cumulative,
            "data": trends_dict
        }

    def save_data_json(self, data: Dict, filename: str):
        """データをJSONファイルとして保存"""
        output_file = self.data_dir / filename
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSONデータを保存しました: {output_file}")

    def generate_html_report(self, analysis_results: Dict, template_path: Optional[str] = None):
        """HTMLレポートを生成"""
        if template_path is None:
            template_path = Path(__file__).parent.parent / "templates" / "report.html"

        template_path = Path(template_path)

        if not template_path.exists():
            # デフォルトテンプレートを作成
            self._create_default_template(template_path)

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        html_content = template.render(**analysis_results)

        output_file = self.output_dir / "report.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"HTMLレポートを生成しました: {output_file}")

    def _create_default_template(self, template_path: Path):
        """デフォルトのHTMLテンプレートを作成"""
        template_path.parent.mkdir(parents=True, exist_ok=True)

        # テンプレートファイルが存在する場合はそれを使用
        if template_path.exists():
            return

        template_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Extended History Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }
        .kpi-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .kpi-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .kpi-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .kpi-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            color: #666;
            border-bottom: 3px solid transparent;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .section {
            margin: 40px 0;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .section img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .chart-container {
            margin: 30px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #667eea;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 My Personal Spotify Wrapped</h1>

        <div class="kpi-section">
            <div class="kpi-card">
                <div class="kpi-label">総再生時間</div>
                <div class="kpi-value">{{ kpis.total_duration_hours }}h</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">総再生回数</div>
                <div class="kpi-value">{{ kpis.total_plays | int }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">有効再生回数</div>
                <div class="kpi-value">{{ kpis.valid_plays | int }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">ユニークアーティスト</div>
                <div class="kpi-value">{{ kpis.unique_artists | int }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">ユニークトラック</div>
                <div class="kpi-value">{{ kpis.unique_tracks | int }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Listen Through Rate</div>
                <div class="kpi-value">{{ kpis.listen_through_rate }}%</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('count')">再生数ベース</button>
            <button class="tab" onclick="switchTab('duration')">再生時間ベース</button>
        </div>

        <div id="count-tab" class="tab-content active">
            <div class="section">
                <h2>Top Artists (再生数)</h2>
                <img src="images/top_artists_count.png" alt="Top Artists by Count">
            </div>

            <div class="section">
                <h2>Top Tracks (再生数)</h2>
                <img src="images/top_tracks_count.png" alt="Top Tracks by Count">
            </div>
        </div>

        <div id="duration-tab" class="tab-content">
            <div class="section">
                <h2>Top Artists (再生時間)</h2>
                <img src="images/top_artists_duration.png" alt="Top Artists by Duration">
            </div>

            <div class="section">
                <h2>Top Tracks (再生時間)</h2>
                <img src="images/top_tracks_duration.png" alt="Top Tracks by Duration">
            </div>
        </div>

        <div class="section">
            <h2>Peak Listening Time</h2>
            <img src="images/peak_listening_time.png" alt="Peak Listening Time">
        </div>

        <div class="section">
            <h2>Seasonal Trends</h2>
            <img src="images/seasonal_trends.png" alt="Seasonal Trends">
        </div>
    </div>

    <script>
        function switchTab(tab) {
            // タブ切り替え
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
        }
    </script>
</body>
</html>"""

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

