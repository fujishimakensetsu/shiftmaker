# -*- coding: utf-8 -*-
"""
モデル（データ管理）
"""

from .data_store import (
    get_firestore_client,
    load_data,
    save_data,
    get_locations,
    set_locations,
    get_staff,
    set_staff,
    get_ng_days,
    set_ng_days,
    get_exceptions,
    set_exceptions,
    save_shift,
    load_shift,
    delete_shift,
    list_shifts,
)
