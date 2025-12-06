"""Data Loader: JSONファイルの読み込みと結合、DataFrame化"""
import json
import pandas as pd
from pathlib import Path
from typing import List


class DataLoader:
    """Spotify Extended Streaming HistoryのJSONファイルを読み込んでDataFrameに変換"""

    def __init__(self, data_dir: str = "Spotify Extended Streaming History"):
        self.data_dir = Path(data_dir)

    def load_all_audio_history(self) -> pd.DataFrame:
        """オーディオ履歴の全JSONファイルを読み込んで結合"""
        audio_files = sorted(
            self.data_dir.glob("Streaming_History_Audio_*.json")
        )

        if not audio_files:
            raise FileNotFoundError(
                f"オーディオ履歴ファイルが見つかりません: {self.data_dir}"
            )

        all_data = []
        for file_path in audio_files:
            print(f"読み込み中: {file_path.name}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data.extend(data)

        df = pd.DataFrame(all_data)
        print(f"合計 {len(df):,} 件のレコードを読み込みました")

        return self._clean_data(df)

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """データのクリーニングと正規化"""
        # タイムスタンプをdatetimeに変換
        df["ts"] = pd.to_datetime(df["ts"], utc=True)

        # オーディオのみを対象（episode_name, audiobook_titleがnullのもの）
        df = df[
            df["episode_name"].isna() &
            df["audiobook_title"].isna()
        ].copy()

        # 必要なカラムのみを保持
        required_columns = [
            "ts",
            "ms_played",
            "master_metadata_track_name",
            "master_metadata_album_artist_name",
            "master_metadata_album_album_name",
            "spotify_track_uri",
            "reason_start",
            "reason_end",
            "skipped",
        ]

        # 存在するカラムのみを選択
        available_columns = [col for col in required_columns if col in df.columns]
        df = df[available_columns].copy()

        # 欠損値の処理
        df["master_metadata_track_name"] = df["master_metadata_track_name"].fillna("Unknown Track")
        df["master_metadata_album_artist_name"] = df["master_metadata_album_artist_name"].fillna("Unknown Artist")
        df["master_metadata_album_album_name"] = df["master_metadata_album_album_name"].fillna("Unknown Album")

        # 日付関連のカラムを追加
        df["date"] = df["ts"].dt.date
        df["year"] = df["ts"].dt.year
        df["month"] = df["ts"].dt.month
        df["day_of_week"] = df["ts"].dt.dayofweek  # 0=Monday, 6=Sunday
        df["hour"] = df["ts"].dt.hour

        # 再生時間を分・時間に変換
        df["minutes_played"] = df["ms_played"] / 60000
        df["hours_played"] = df["ms_played"] / 3600000

        print(f"クリーニング後: {len(df):,} 件のレコード")
        return df

