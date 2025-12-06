"""Analyzer: 集計・計算ロジック"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime


class Analyzer:
    """再生履歴データの解析"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.MIN_PLAY_TIME_MS = 30000  # 30秒

    def calculate_kpis(self) -> Dict[str, any]:
        """基本KPIを計算"""
        total_plays = len(self.df)
        total_duration_ms = self.df["ms_played"].sum()
        total_duration_hours = total_duration_ms / 3600000

        # 再生数（30秒以上）
        valid_plays = len(self.df[self.df["ms_played"] >= self.MIN_PLAY_TIME_MS])

        # ユニークなアーティスト・トラック・アルバム数
        unique_artists = self.df["master_metadata_album_artist_name"].nunique()
        unique_tracks = self.df["master_metadata_track_name"].nunique()
        unique_albums = self.df["master_metadata_album_album_name"].nunique()

        # Listen Through Rate
        completed_plays = len(self.df[self.df["reason_end"] == "trackdone"])
        listen_through_rate = (completed_plays / total_plays * 100) if total_plays > 0 else 0

        return {
            "total_plays": total_plays,
            "valid_plays": valid_plays,
            "total_duration_hours": round(total_duration_hours, 2),
            "unique_artists": unique_artists,
            "unique_tracks": unique_tracks,
            "unique_albums": unique_albums,
            "listen_through_rate": round(listen_through_rate, 2),
        }

    def get_top_artists_by_count(self, top_n: int = 10) -> pd.DataFrame:
        """再生数ベースのトップアーティスト"""
        valid_df = self.df[self.df["ms_played"] >= self.MIN_PLAY_TIME_MS]
        top = (
            valid_df.groupby("master_metadata_album_artist_name")
            .size()
            .reset_index(name="play_count")
            .sort_values("play_count", ascending=False)
            .head(top_n)
        )
        return top

    def get_top_artists_by_duration(self, top_n: int = 10) -> pd.DataFrame:
        """再生時間ベースのトップアーティスト"""
        top = (
            self.df.groupby("master_metadata_album_artist_name")
            .agg({
                "ms_played": "sum",
                "master_metadata_track_name": "count"
            })
            .reset_index()
            .rename(columns={
                "ms_played": "total_ms_played",
                "master_metadata_track_name": "play_count"
            })
        )
        top["total_hours"] = top["total_ms_played"] / 3600000
        top = top.sort_values("total_hours", ascending=False).head(top_n)
        return top

    def get_top_tracks_by_count(self, top_n: int = 10) -> pd.DataFrame:
        """再生数ベースのトップトラック"""
        valid_df = self.df[self.df["ms_played"] >= self.MIN_PLAY_TIME_MS]
        top = (
            valid_df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])
            .size()
            .reset_index(name="play_count")
            .sort_values("play_count", ascending=False)
            .head(top_n)
        )
        return top

    def get_top_tracks_by_duration(self, top_n: int = 10) -> pd.DataFrame:
        """再生時間ベースのトップトラック"""
        top = (
            self.df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])
            .agg({
                "ms_played": "sum",
            })
            .reset_index()
        )
        top["total_hours"] = top["ms_played"] / 3600000
        top = top.sort_values("total_hours", ascending=False).head(top_n)
        return top

    def get_top_albums_by_count(self, top_n: int = 10) -> pd.DataFrame:
        """再生数ベースのトップアルバム"""
        valid_df = self.df[self.df["ms_played"] >= self.MIN_PLAY_TIME_MS]
        top = (
            valid_df.groupby(["master_metadata_album_album_name", "master_metadata_album_artist_name"])
            .size()
            .reset_index(name="play_count")
            .sort_values("play_count", ascending=False)
            .head(top_n)
        )
        return top

    def get_top_albums_by_duration(self, top_n: int = 10) -> pd.DataFrame:
        """再生時間ベースのトップアルバム"""
        top = (
            self.df.groupby(["master_metadata_album_album_name", "master_metadata_album_artist_name"])
            .agg({
                "ms_played": "sum",
            })
            .reset_index()
        )
        top["total_hours"] = top["ms_played"] / 3600000
        top = top.sort_values("total_hours", ascending=False).head(top_n)
        return top

    def get_peak_listening_time(self) -> pd.DataFrame:
        """時間帯×曜日のヒートマップ用データ"""
        heatmap_data = (
            self.df.groupby(["day_of_week", "hour"])
            .agg({
                "ms_played": "sum",
                "master_metadata_track_name": "count"
            })
            .reset_index()
        )
        heatmap_data["total_hours"] = heatmap_data["ms_played"] / 3600000
        heatmap_data["play_count"] = heatmap_data["master_metadata_track_name"]
        return heatmap_data

    def get_seasonal_trends(self) -> pd.DataFrame:
        """月ごとの再生推移"""
        trends = (
            self.df.groupby(["year", "month"])
            .agg({
                "ms_played": "sum",
                "master_metadata_track_name": "count"
            })
            .reset_index()
        )
        trends["total_hours"] = trends["ms_played"] / 3600000
        trends["play_count"] = trends["master_metadata_track_name"]
        trends["date"] = pd.to_datetime(trends[["year", "month"]].assign(day=1))
        return trends.sort_values("date")

    def get_listen_through_rate_by_artist(self, top_n: int = 20) -> pd.DataFrame:
        """アーティスト別のListen Through Rate"""
        artist_stats = (
            self.df.groupby("master_metadata_album_artist_name")
            .agg({
                "reason_end": lambda x: (x == "trackdone").sum(),
                "master_metadata_track_name": "count"
            })
            .reset_index()
        )
        artist_stats.columns = ["artist", "completed", "total"]
        artist_stats["rate"] = (artist_stats["completed"] / artist_stats["total"] * 100).round(2)
        artist_stats = artist_stats[artist_stats["total"] >= 10]  # 最低10回再生
        return artist_stats.sort_values("rate", ascending=False).head(top_n)

    def get_available_years(self) -> List[int]:
        """データに含まれる年リストを取得"""
        return sorted(self.df["year"].unique().tolist())

    def get_yearly_kpis(self) -> Dict[int, Dict[str, any]]:
        """各年のKPIを計算"""
        yearly_kpis = {}
        for year in self.get_available_years():
            year_df = self.df[self.df["year"] == year]
            year_analyzer = Analyzer(year_df)
            yearly_kpis[year] = year_analyzer.calculate_kpis()
        return yearly_kpis

    def get_top_artists_by_year(self, year: int, metric: str = "count", top_n: int = 10) -> pd.DataFrame:
        """年ごとのトップアーティスト"""
        year_df = self.df[self.df["year"] == year]
        if metric == "count":
            return Analyzer(year_df).get_top_artists_by_count(top_n)
        else:
            return Analyzer(year_df).get_top_artists_by_duration(top_n)

    def get_top_tracks_by_year(self, year: int, metric: str = "count", top_n: int = 10) -> pd.DataFrame:
        """年ごとのトップトラック"""
        year_df = self.df[self.df["year"] == year]
        if metric == "count":
            return Analyzer(year_df).get_top_tracks_by_count(top_n)
        else:
            return Analyzer(year_df).get_top_tracks_by_duration(top_n)

    def get_top_albums_by_year(self, year: int, metric: str = "count", top_n: int = 10) -> pd.DataFrame:
        """年ごとのトップアルバム"""
        year_df = self.df[self.df["year"] == year]
        if metric == "count":
            return Analyzer(year_df).get_top_albums_by_count(top_n)
        else:
            return Analyzer(year_df).get_top_albums_by_duration(top_n)

    def get_peak_listening_time_by_year(self, year: int) -> pd.DataFrame:
        """年ごとのピークリスニング時間"""
        year_df = self.df[self.df["year"] == year]
        return Analyzer(year_df).get_peak_listening_time()

    def get_artist_trends(self, top_n: int = 10, cumulative: bool = False) -> pd.DataFrame:
        """アーティストごとの再生推移（月次）"""
        # トップアーティストを取得（全期間の再生時間ベース）
        top_artists = self.get_top_artists_by_duration(top_n)
        top_artist_names = top_artists["master_metadata_album_artist_name"].tolist()

        # 月ごとの集計
        trends = []
        for year in self.get_available_years():
            year_df = self.df[self.df["year"] == year]
            for month in range(1, 13):
                month_df = year_df[year_df["month"] == month]
                if len(month_df) == 0:
                    continue

                for artist in top_artist_names:
                    artist_df = month_df[month_df["master_metadata_album_artist_name"] == artist]
                    if len(artist_df) > 0:
                        total_ms = artist_df["ms_played"].sum()
                        play_count = len(artist_df[artist_df["ms_played"] >= self.MIN_PLAY_TIME_MS])
                        trends.append({
                            "year": year,
                            "month": month,
                            "artist": artist,
                            "total_hours": total_ms / 3600000,
                            "play_count": play_count,
                            "date": pd.to_datetime(f"{year}-{month:02d}-01")
                        })

        trends_df = pd.DataFrame(trends)

        if cumulative:
            # 累積値を計算
            trends_df = trends_df.sort_values(["artist", "date"])
            trends_df["cumulative_hours"] = trends_df.groupby("artist")["total_hours"].cumsum()
            trends_df["cumulative_plays"] = trends_df.groupby("artist")["play_count"].cumsum()

        return trends_df


