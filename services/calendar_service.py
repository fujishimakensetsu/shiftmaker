# -*- coding: utf-8 -*-
"""
カレンダー生成サービス
"""

import calendar
from datetime import date
import jpholiday

from models import get_locations, get_exceptions


def get_calendar_data(year, month, month_exceptions=None):
    """指定年月のカレンダーデータを生成"""
    locations = get_locations()
    if month_exceptions is None:
        exceptions = get_exceptions()
        key = f"{year}-{month:02d}"
        month_exceptions = exceptions.get(key, {})

    cal_data = []
    _, num_days = calendar.monthrange(year, month)

    for day in range(1, num_days + 1):
        d = date(year, month, day)
        weekday = d.weekday()
        is_holiday = jpholiday.is_holiday(d)
        holiday_name = jpholiday.is_holiday_name(d)
        date_str = d.isoformat()

        day_info = {
            "date": date_str,
            "day": day,
            "weekday": weekday,
            "weekday_name": ['月', '火', '水', '木', '金', '土', '日'][weekday],
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "locations": []
        }

        for loc in locations:
            loc_id_str = str(loc['id'])
            loc_exceptions = month_exceptions.get(loc_id_str, {"add": [], "remove": []})
            add_dates = loc_exceptions.get("add", [])
            remove_dates = loc_exceptions.get("remove", [])

            # 定休日チェック
            closed_days = loc.get('closed_days', [])
            is_closed_day = weekday in closed_days

            is_working = False
            if is_closed_day:
                is_working = False
            elif is_holiday:
                is_working = loc.get('work_on_holidays', True)
            else:
                is_working = weekday in loc.get('working_days', [5, 6])

            if date_str in add_dates:
                is_working = True
            if date_str in remove_dates:
                is_working = False

            day_info['locations'].append({
                "id": loc['id'],
                "name": loc['name'],
                "is_working": is_working,
                "is_closed_day": is_closed_day,
                "min_staff": loc.get('min_staff', 1),
                "max_staff": loc.get('max_staff', 2),
                "part_time_priority": loc.get('part_time_priority', False),
                "flexible_staffing": loc.get('flexible_staffing', False)
            })

        cal_data.append(day_info)

    return cal_data
