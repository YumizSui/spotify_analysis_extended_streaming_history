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

    def get_audio_aura_data(self, enriched_df: pd.DataFrame, top_n: int = 50) -> Dict[str, any]:
        """案1: Audio Aura - トップ曲のオーディオ特徴量を集計"""
        # オーディオ特徴量が含まれるデータのみを対象
        audio_features_cols = [
            "danceability", "energy", "valence", "acousticness", "tempo"
        ]

        # 特徴量が存在するか確認
        available_features = [col for col in audio_features_cols if col in enriched_df.columns]

        if not available_features:
            return {
                "features": {},
                "average": {},
                "count": 0
            }

        # トップN曲を選定（再生時間ベース）
        top_tracks = (
            enriched_df.groupby(["master_metadata_track_name", "master_metadata_album_artist_name"])
            .agg({"ms_played": "sum"})
            .reset_index()
            .sort_values("ms_played", ascending=False)
            .head(top_n)
        )

        # トップ曲の特徴量を抽出
        top_tracks_with_features = enriched_df.merge(
            top_tracks[["master_metadata_track_name", "master_metadata_album_artist_name"]],
            on=["master_metadata_track_name", "master_metadata_album_artist_name"],
            how="inner"
        )

        # 重複を除去（同じトラックの特徴量は1つだけ）
        top_tracks_with_features = top_tracks_with_features.drop_duplicates(
            subset=["master_metadata_track_name", "master_metadata_album_artist_name"]
        )

        # 平均値を計算
        averages = {}
        for feature in available_features:
            values = top_tracks_with_features[feature].dropna()
            if len(values) > 0:
                if feature == "tempo":
                    averages[feature] = values.mean()
                else:
                    averages[feature] = values.mean()

        return {
            "features": available_features,
            "average": averages,
            "count": len(top_tracks_with_features)
        }

    def get_genre_distribution(self, enriched_df: pd.DataFrame) -> Dict[str, any]:
        """案4: Genre Pie with Depth - ジャンルの詳細内訳"""
        # ジャンル情報が含まれるデータのみを対象
        if "genres" not in enriched_df.columns:
            return {"genres": [], "count": 0}

        # ジャンルを展開（リスト形式の場合）
        genre_list = []
        for genres in enriched_df["genres"].dropna():
            if isinstance(genres, list):
                genre_list.extend(genres)
            elif isinstance(genres, str):
                # カンマ区切りの場合
                genre_list.extend([g.strip() for g in genres.split(",")])

        if not genre_list:
            return {"genres": [], "count": 0}

        # ジャンルごとの再生時間を集計
        genre_df = pd.DataFrame({"genre": genre_list})

        # 各ジャンルに対応する再生時間を計算
        genre_playtime = {}
        for idx, row in enriched_df.iterrows():
            if pd.notna(row.get("genres")):
                genres = row["genres"]
                if isinstance(genres, list):
                    for genre in genres:
                        genre_playtime[genre] = genre_playtime.get(genre, 0) + row["ms_played"]
                elif isinstance(genres, str):
                    for genre in [g.strip() for g in genres.split(",")]:
                        genre_playtime[genre] = genre_playtime.get(genre, 0) + row["ms_played"]

        # DataFrameに変換
        genre_stats = pd.DataFrame([
            {"genre": genre, "total_hours": ms / 3600000, "play_count": 1}
            for genre, ms in genre_playtime.items()
        ])

        # 再生回数も集計
        genre_counts = pd.Series(genre_list).value_counts()
        genre_stats = genre_stats.merge(
            genre_counts.reset_index(),
            left_on="genre",
            right_on="index",
            how="left"
        )
        genre_stats["play_count"] = genre_stats[0].fillna(1)
        genre_stats = genre_stats.drop(columns=["index", 0])

        # トップジャンルを取得
        top_genres = genre_stats.sort_values("total_hours", ascending=False).head(30)

        return {
            "genres": top_genres.to_dict("records"),
            "total_unique_genres": len(genre_stats),
            "count": len(genre_list)
        }

