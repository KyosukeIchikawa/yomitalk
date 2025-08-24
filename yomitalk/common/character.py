"""VOICEVOXキャラクター定義モジュール。

このモジュールではVOICEVOXキャラクターのEnum定義とそれに関連する機能を提供します。
"""

from enum import Enum


class Character(Enum):
    """VOICEVOXキャラクター定義のEnum"""

    ZUNDAMON = ("ずんだもん", 3, "0.vvm", 0.0)  # ずんだもん (sweet)
    SHIKOKU_METAN = ("四国めたん", 2, "0.vvm", 0.0)  # 四国めたん (normal)
    KYUSHU_SORA = ("九州そら", 16, "2.vvm", 0.0)  # 九州そら (normal)
    CHUGOKU_USAGI = ("中国うさぎ", 61, "3.vvm", 0.0)  # 中国うさぎ (normal)
    CHUBU_TSURUGI = ("中部つるぎ", 94, "18.vvm", 0.0)  # 中部つるぎ (normal)
    TOHOKU_ZUNKO = ("東北ずん子", 107, "21.vvm", 0.0)  # 東北ずん子 (normal)
    TOHOKU_KIRITAN = ("東北きりたん", 108, "21.vvm", 0.05)  # 東北きりたん (normal) - ピッチを5%上げる
    TOHOKU_ITAKO = ("東北イタコ", 109, "21.vvm", 0.0)  # 東北イタコ (normal)

    def __init__(self, display_name: str, style_id: int, model_file: str, pitch_scale: float):
        self.display_name = display_name
        self.style_id = style_id
        self.model_file = model_file
        self.pitch_scale = pitch_scale


DISPLAY_NAMES = [character.display_name for character in Character]
STYLE_ID_BY_NAME = {character.display_name: character.style_id for character in Character}

# キャラクターが必要とする音声モデルファイル（.vvm）の一覧
REQUIRED_MODEL_FILES = sorted(set(character.model_file for character in Character))
