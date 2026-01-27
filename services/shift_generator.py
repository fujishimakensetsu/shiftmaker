# -*- coding: utf-8 -*-
"""
シフト生成アルゴリズム
"""

from models import get_locations, get_staff
from .calendar_service import get_calendar_data


def generate_shift(year, month, ng_days_data, month_exceptions):
    """シフトを自動生成"""
    locations = get_locations()
    staff_list = get_staff()
    cal_data = get_calendar_data(year, month, month_exceptions)

    staff_counts = {s['id']: 0 for s in staff_list}
    shift_result = {}

    for day_info in cal_data:
        date_str = day_info['date']
        shift_result[date_str] = {}

        for loc_info in day_info['locations']:
            loc_id = loc_info['id']
            shift_result[date_str][loc_id] = []

            if not loc_info['is_working']:
                continue

            min_required = loc_info['min_staff']
            max_allowed = loc_info['max_staff']
            assigned = []

            available_staff = []
            for s in staff_list:
                staff_id = s['id']
                staff_id_str = str(staff_id)

                # パートの場合、所属拠点チェック
                if s['type'] == 'パート':
                    assigned_locs = s.get('assigned_locations', [])
                    if assigned_locs and loc_id not in assigned_locs:
                        continue

                staff_ng_days = ng_days_data.get(staff_id_str, [])
                if date_str in staff_ng_days:
                    continue

                if staff_counts[staff_id] >= s['max_days']:
                    continue

                already_assigned_today = False
                for other_loc_id, other_assigned in shift_result[date_str].items():
                    if staff_id in other_assigned:
                        already_assigned_today = True
                        break
                if already_assigned_today:
                    continue

                available_staff.append(s)

            if loc_info['part_time_priority']:
                part_timers = [s for s in available_staff if s['type'] == 'パート']
                regulars = [s for s in available_staff if s['type'] == '社員']

                part_timers.sort(key=lambda s: staff_counts[s['id']])
                regulars.sort(key=lambda s: staff_counts[s['id']])

                # パート優先枠でも、まず社員を1人確保する
                for s in regulars:
                    if len(assigned) >= 1:
                        break
                    assigned.append(s['id'])
                    staff_counts[s['id']] += 1

                # パートは最大1人まで
                for s in part_timers:
                    if len(assigned) >= max_allowed:
                        break
                    assigned.append(s['id'])
                    staff_counts[s['id']] += 1
                    break

                # flexible_staffing: パートがいなければ最小人数を1に減らす
                if loc_info['flexible_staffing']:
                    part_count = len([sid for sid in assigned
                                    if any(s['id'] == sid and s['type'] == 'パート' for s in staff_list)])
                    if part_count == 0 and min_required > 1:
                        min_required = 1

                # 残りの枠を社員で埋める
                for s in regulars:
                    if len(assigned) >= max_allowed:
                        break
                    if len(assigned) >= min_required:
                        break
                    if s['id'] in assigned:
                        continue
                    assigned.append(s['id'])
                    staff_counts[s['id']] += 1
            else:
                available_staff.sort(key=lambda s: staff_counts[s['id']])

                for s in available_staff:
                    if len(assigned) >= max_allowed:
                        break
                    assigned.append(s['id'])
                    staff_counts[s['id']] += 1

            shift_result[date_str][loc_id] = assigned

    return {
        "year": year,
        "month": month,
        "shift": shift_result,
        "staff_counts": staff_counts
    }
