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

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

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

    def plot_top_artists(self, top_artists: pd.DataFrame, metric: str, output_name: str):
        """トップアーティストの棒グラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_artists = top_artists.sort_values(y_col, ascending=True)

        bars = ax.barh(
            range(len(top_artists)),
            top_artists[y_col],
            color=sns.color_palette("husl", len(top_artists))
        )

        ax.set_yticks(range(len(top_artists)))
        ax.set_yticklabels(top_artists["master_metadata_album_artist_name"], fontsize=10)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Artists ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_top_tracks(self, top_tracks: pd.DataFrame, metric: str, output_name: str):
        """トップトラックの棒グラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_tracks = top_tracks.sort_values(y_col, ascending=True)
        labels = [
            f"{row['master_metadata_track_name']}\n({row['master_metadata_album_artist_name']})"
            for _, row in top_tracks.iterrows()
        ]

        bars = ax.barh(
            range(len(top_tracks)),
            top_tracks[y_col],
            color=sns.color_palette("husl", len(top_tracks))
        )

        ax.set_yticks(range(len(top_tracks)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Tracks ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_peak_listening_time(self, heatmap_data: pd.DataFrame, output_name: str):
        """時間帯×曜日のヒートマップ"""
        # ピボットテーブル作成
        pivot = heatmap_data.pivot_table(
            values="total_hours",
            index="day_of_week",
            columns="hour",
            fill_value=0
        )

        # 曜日ラベル
        day_labels = ["月", "火", "水", "木", "金", "土", "日"]
        pivot.index = [day_labels[i] for i in pivot.index]

        fig, ax = plt.subplots(figsize=(14, 6))
        sns.heatmap(
            pivot,
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            cbar_kws={"label": "再生時間 (時間)"},
            ax=ax
        )
        ax.set_xlabel("時間帯", fontsize=12)
        ax.set_ylabel("曜日", fontsize=12)
        ax.set_title("Peak Listening Time", fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_seasonal_trends(self, trends: pd.DataFrame, output_name: str):
        """月ごとの再生推移"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # 再生時間
        ax1.plot(trends["date"], trends["total_hours"], marker="o", linewidth=2, markersize=6)
        ax1.set_xlabel("日付", fontsize=12)
        ax1.set_ylabel("再生時間 (時間)", fontsize=12)
        ax1.set_title("Seasonal Trends - 再生時間", fontsize=14, fontweight="bold")
        ax1.grid(alpha=0.3)
        ax1.tick_params(axis="x", rotation=45)

        # 再生回数
        ax2.plot(trends["date"], trends["play_count"], marker="o", linewidth=2, markersize=6, color="orange")
        ax2.set_xlabel("日付", fontsize=12)
        ax2.set_ylabel("再生回数", fontsize=12)
        ax2.set_title("Seasonal Trends - 再生回数", fontsize=14, fontweight="bold")
        ax2.grid(alpha=0.3)
        ax2.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_audio_aura(self, audio_aura_data: Dict, output_name: str):
        """案1: Audio Aura - レーダーチャート"""
        if not audio_aura_data.get("average"):
            return

        features = audio_aura_data["features"]
        averages = audio_aura_data["average"]

        # レーダーチャート用データ準備
        categories = []
        values = []

        feature_labels = {
            "danceability": "Danceability",
            "energy": "Energy",
            "valence": "Valence",
            "acousticness": "Acousticness",
            "tempo": "Tempo"
        }

        for feature in features:
            if feature in averages:
                categories.append(feature_labels.get(feature, feature))
                # Tempoは正規化（0-200の範囲を0-1に）
                if feature == "tempo":
                    values.append(averages[feature] / 200)
                else:
                    values.append(averages[feature])

        if not categories:
            return

        # レーダーチャート作成
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="Audio Aura",
            line_color="purple"
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Audio Aura - オーディオ特徴量",
            font=dict(size=14)
        )

        fig.write_html(str(self.images_dir / output_name))

        # 静的画像も生成
        fig_static = plt.figure(figsize=(10, 10))
        ax = fig_static.add_subplot(111, projection="polar")

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_plot = values + [values[0]]  # 閉じる
        angles_plot = angles + [angles[0]]

        ax.plot(angles_plot, values_plot, "o-", linewidth=2, color="purple")
        ax.fill(angles_plot, values_plot, alpha=0.25, color="purple")
        ax.set_xticks(angles)
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title("Audio Aura - オーディオ特徴量", fontsize=14, fontweight="bold", pad=20)
        ax.grid(True)

        plt.tight_layout()
        plt.savefig(self.images_dir / f"{output_name.replace('.html', '.png')}", dpi=150, bbox_inches="tight")
        plt.close()

    def plot_genre_pie(self, genre_data: Dict, output_name: str):
        """案4: Genre Pie with Depth - ジャンルのパイチャート"""
        if not genre_data.get("genres"):
            return

        genres_df = pd.DataFrame(genre_data["genres"])
        top_20 = genres_df.head(20)

        fig, ax = plt.subplots(figsize=(14, 10))

        colors = sns.color_palette("husl", len(top_20))
        wedges, texts, autotexts = ax.pie(
            top_20["total_hours"],
            labels=top_20["genre"],
            autopct="%1.1f%%",
            colors=colors,
            startangle=90
        )

        # ラベルサイズ調整
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color("white")
            autotext.set_weight("bold")

        ax.set_title("Genre Distribution - ジャンル分布", fontsize=14, fontweight="bold", pad=20)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_top_albums(self, top_albums: pd.DataFrame, metric: str, output_name: str):
        """トップアルバムの棒グラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_albums = top_albums.sort_values(y_col, ascending=True)
        labels = [
            f"{row['master_metadata_album_album_name']}\n({row['master_metadata_album_artist_name']})"
            for _, row in top_albums.iterrows()
        ]

        bars = ax.barh(
            range(len(top_albums)),
            top_albums[y_col],
            color=sns.color_palette("husl", len(top_albums))
        )

        ax.set_yticks(range(len(top_albums)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Albums ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_top_artists_by_year(self, top_artists: pd.DataFrame, metric: str, year: int, output_name: str):
        """年ごとのトップアーティストグラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_artists = top_artists.sort_values(y_col, ascending=True)

        bars = ax.barh(
            range(len(top_artists)),
            top_artists[y_col],
            color=sns.color_palette("husl", len(top_artists))
        )

        ax.set_yticks(range(len(top_artists)))
        ax.set_yticklabels(top_artists["master_metadata_album_artist_name"], fontsize=10)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Artists {year} ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_top_tracks_by_year(self, top_tracks: pd.DataFrame, metric: str, year: int, output_name: str):
        """年ごとのトップトラックグラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_tracks = top_tracks.sort_values(y_col, ascending=True)
        labels = [
            f"{row['master_metadata_track_name']}\n({row['master_metadata_album_artist_name']})"
            for _, row in top_tracks.iterrows()
        ]

        bars = ax.barh(
            range(len(top_tracks)),
            top_tracks[y_col],
            color=sns.color_palette("husl", len(top_tracks))
        )

        ax.set_yticks(range(len(top_tracks)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Tracks {year} ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_top_albums_by_year(self, top_albums: pd.DataFrame, metric: str, year: int, output_name: str):
        """年ごとのトップアルバムグラフ"""
        fig, ax = plt.subplots(figsize=(12, 8))

        if metric == "count":
            y_col = "play_count"
            ylabel = "再生回数"
        else:
            y_col = "total_hours"
            ylabel = "再生時間 (時間)"

        top_albums = top_albums.sort_values(y_col, ascending=True)
        labels = [
            f"{row['master_metadata_album_album_name']}\n({row['master_metadata_album_artist_name']})"
            for _, row in top_albums.iterrows()
        ]

        bars = ax.barh(
            range(len(top_albums)),
            top_albums[y_col],
            color=sns.color_palette("husl", len(top_albums))
        )

        ax.set_yticks(range(len(top_albums)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(ylabel, fontsize=12)
        ax.set_title(f"Top Albums {year} ({metric.title()} Base)", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_peak_listening_time_by_year(self, heatmap_data: pd.DataFrame, year: int, output_name: str):
        """年ごとの時間帯×曜日のヒートマップ"""
        # ピボットテーブル作成
        pivot = heatmap_data.pivot_table(
            values="total_hours",
            index="day_of_week",
            columns="hour",
            fill_value=0
        )

        # 曜日ラベル
        day_labels = ["月", "火", "水", "木", "金", "土", "日"]
        pivot.index = [day_labels[i] for i in pivot.index]

        fig, ax = plt.subplots(figsize=(14, 6))
        sns.heatmap(
            pivot,
            annot=True,
            fmt=".1f",
            cmap="YlOrRd",
            cbar_kws={"label": "再生時間 (時間)"},
            ax=ax
        )
        ax.set_xlabel("時間帯", fontsize=12)
        ax.set_ylabel("曜日", fontsize=12)
        ax.set_title(f"Peak Listening Time {year}", fontsize=14, fontweight="bold")

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

    def plot_genre_distribution_by_year(self, genre_data: Dict, year: int, output_name: str):
        """年ごとのジャンル分布グラフ"""
        if not genre_data.get("genres"):
            return

        genres_df = pd.DataFrame(genre_data["genres"])
        top_20 = genres_df.head(20)

        fig, ax = plt.subplots(figsize=(14, 10))

        colors = sns.color_palette("husl", len(top_20))
        wedges, texts, autotexts = ax.pie(
            top_20["total_hours"],
            labels=top_20["genre"],
            autopct="%1.1f%%",
            colors=colors,
            startangle=90
        )

        # ラベルサイズ調整
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color("white")
            autotext.set_weight("bold")

        ax.set_title(f"Genre Distribution {year} - ジャンル分布", fontsize=14, fontweight="bold", pad=20)

        plt.tight_layout()
        plt.savefig(self.images_dir / output_name, dpi=150, bbox_inches="tight")
        plt.close()

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

    def plot_genre_trends_plotly(self, trends_df: pd.DataFrame, output_name: str, cumulative: bool = False):
        """ジャンルごとの再生推移（Plotly）"""
        if trends_df.empty:
            return

        fig = go.Figure()

        genres = trends_df["genre"].unique()
        colors = px.colors.qualitative.Set3

        for i, genre in enumerate(genres):
            genre_data = trends_df[trends_df["genre"] == genre].sort_values("date")

            if cumulative:
                y_col = "cumulative_hours"
                y_label = "累積再生時間 (時間)"
            else:
                y_col = "total_hours"
                y_label = "再生時間 (時間)"

            fig.add_trace(go.Scatter(
                x=genre_data["date"],
                y=genre_data[y_col],
                mode="lines+markers",
                name=genre,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6)
            ))

        fig.update_layout(
            title="ジャンルごとの再生推移",
            xaxis_title="日付",
            yaxis_title=y_label,
            hovermode="x unified",
            height=600,
            font=dict(size=12)
        )

        fig.write_html(str(self.images_dir / output_name))

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

