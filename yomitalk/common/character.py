"""VOICEVOXキャラクター定義モジュール。

このモジュールではVOICEVOXキャラクターのEnum定義とそれに関連する機能を提供します。
"""

from enum import Enum


class Character(Enum):
    """VOICEVOXキャラクター定義のEnum"""

    ZUNDAMON = ("ずんだもん", 3)  # ずんだもん (sweet)
    SHIKOKU_METAN = ("四国めたん", 2)  # 四国めたん (normal)
    KYUSHU_SORA = ("九州そら", 16)  # 九州そら (normal)
    CHUGOKU_USAGI = ("中国うさぎ", 61)  # 中国うさぎ (normal)
    CHUBU_TSURUGI = ("中部つるぎ", 94)  # 中部つるぎ (normal)

    def __init__(self, display_name: str, style_id: int):
        self.display_name = display_name
        self.style_id = style_id


DISPLAY_NAMES = [character.display_name for character in Character]
STYLE_ID_BY_NAME = {
    character.display_name: character.style_id for character in Character
}
