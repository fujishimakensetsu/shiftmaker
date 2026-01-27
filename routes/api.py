# -*- coding: utf-8 -*-
"""
APIルーティング
"""

import json
from datetime import datetime
from io import BytesIO
from copy import deepcopy

from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required

from config import DEFAULT_DATA
from models import (
    load_data, save_data,
    get_locations, set_locations,
    get_staff, set_staff,
    get_ng_days, set_ng_days,
    get_exceptions, set_exceptions,
    save_shift, load_shift, delete_shift, list_shifts
)
from services import (
    get_calendar_data,
    generate_shift,
    create_excel_shift,
    create_pdf_shift
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


# =============================================================================
# 拠点管理
# =============================================================================

@api_bp.route('/locations', methods=['GET'])
@login_required
def api_get_locations():
    return jsonify(get_locations())


@api_bp.route('/locations', methods=['POST'])
@login_required
def api_add_location():
    data = request.json
    locations = get_locations()

    max_id = max([loc['id'] for loc in locations], default=0)
    new_location = {
        "id": max_id + 1,
        "name": data.get('name', '新規拠点'),
        "working_days": data.get('working_days', [5, 6]),
        "closed_days": data.get('closed_days', []),
        "work_on_holidays": data.get('work_on_holidays', True),
        "min_staff": data.get('min_staff', 1),
        "max_staff": data.get('max_staff', 2),
        "part_time_priority": data.get('part_time_priority', False),
        "flexible_staffing": data.get('flexible_staffing', False)
    }
    locations.append(new_location)
    set_locations(locations)
    return jsonify(new_location)


@api_bp.route('/locations/<int:loc_id>', methods=['PUT'])
@login_required
def api_update_location(loc_id):
    data = request.json
    locations = get_locations()

    for loc in locations:
        if loc['id'] == loc_id:
            loc['name'] = data.get('name', loc['name'])
            loc['working_days'] = data.get('working_days', loc.get('working_days', [5, 6]))
            loc['closed_days'] = data.get('closed_days', loc.get('closed_days', []))
            loc['work_on_holidays'] = data.get('work_on_holidays', loc.get('work_on_holidays', True))
            loc['min_staff'] = data.get('min_staff', loc.get('min_staff', 1))
            loc['max_staff'] = data.get('max_staff', loc.get('max_staff', 2))
            loc['part_time_priority'] = data.get('part_time_priority', loc['part_time_priority'])
            loc['flexible_staffing'] = data.get('flexible_staffing', loc['flexible_staffing'])
            set_locations(locations)
            return jsonify(loc)

    return jsonify({"error": "拠点が見つかりません"}), 404


@api_bp.route('/locations/<int:loc_id>', methods=['DELETE'])
@login_required
def api_delete_location(loc_id):
    locations = get_locations()
    locations = [loc for loc in locations if loc['id'] != loc_id]
    set_locations(locations)
    return jsonify({"success": True})


# =============================================================================
# スタッフ管理
# =============================================================================

@api_bp.route('/staff', methods=['GET'])
@login_required
def api_get_staff():
    return jsonify(get_staff())


@api_bp.route('/staff', methods=['POST'])
@login_required
def api_add_staff():
    data = request.json
    staff_list = get_staff()

    max_id = max([s['id'] for s in staff_list], default=0)
    new_staff = {
        "id": max_id + 1,
        "name": data.get('name', '新規スタッフ'),
        "type": data.get('type', '社員'),
        "max_days": data.get('max_days', 31),
        "assigned_locations": data.get('assigned_locations', [])
    }
    staff_list.append(new_staff)
    set_staff(staff_list)
    return jsonify(new_staff)


@api_bp.route('/staff/<int:staff_id>', methods=['PUT'])
@login_required
def api_update_staff(staff_id):
    data = request.json
    staff_list = get_staff()

    for s in staff_list:
        if s['id'] == staff_id:
            s['name'] = data.get('name', s['name'])
            s['type'] = data.get('type', s['type'])
            s['max_days'] = data.get('max_days', s['max_days'])
            s['assigned_locations'] = data.get('assigned_locations', s.get('assigned_locations', []))
            set_staff(staff_list)
            return jsonify(s)

    return jsonify({"error": "スタッフが見つかりません"}), 404


@api_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
@login_required
def api_delete_staff(staff_id):
    staff_list = get_staff()
    staff_list = [s for s in staff_list if s['id'] != staff_id]
    set_staff(staff_list)
    return jsonify({"success": True})


# =============================================================================
# NG日・例外日管理
# =============================================================================

@api_bp.route('/ng_days', methods=['GET'])
@login_required
def api_get_ng_days():
    return jsonify(get_ng_days())


@api_bp.route('/ng_days', methods=['POST'])
@login_required
def api_set_ng_days():
    data = request.json
    set_ng_days(data)
    return jsonify({"success": True})


@api_bp.route('/exceptions', methods=['GET'])
@login_required
def api_get_exceptions():
    return jsonify(get_exceptions())


@api_bp.route('/exceptions/<int:year>/<int:month>', methods=['GET'])
@login_required
def api_get_month_exceptions(year, month):
    exceptions = get_exceptions()
    key = f"{year}-{month:02d}"
    return jsonify(exceptions.get(key, {}))


@api_bp.route('/exceptions/<int:year>/<int:month>', methods=['POST'])
@login_required
def api_set_month_exceptions(year, month):
    data = request.json
    exceptions = get_exceptions()
    key = f"{year}-{month:02d}"
    exceptions[key] = data
    set_exceptions(exceptions)
    return jsonify({"success": True})


# =============================================================================
# 設定インポート/エクスポート・リセット
# =============================================================================

@api_bp.route('/export_settings', methods=['GET'])
@login_required
def api_export_settings():
    data = load_data()
    data['export_date'] = datetime.now().isoformat()

    output = BytesIO()
    output.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'shift_settings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )


@api_bp.route('/import_settings', methods=['POST'])
@login_required
def api_import_settings():
    if 'file' not in request.files:
        return jsonify({"error": "ファイルがありません"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "ファイルが選択されていません"}), 400

    try:
        content = file.read().decode('utf-8')
        settings = json.loads(content)

        data = load_data()
        if 'locations' in settings:
            data['locations'] = settings['locations']
        if 'staff' in settings:
            data['staff'] = settings['staff']
        if 'ng_days' in settings:
            data['ng_days'] = settings['ng_days']
        if 'exceptions' in settings:
            data['exceptions'] = settings['exceptions']

        save_data(data)
        return jsonify({"success": True, "message": "設定をインポートしました"})
    except json.JSONDecodeError:
        return jsonify({"error": "無効なJSONファイルです"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/reset', methods=['POST'])
@login_required
def api_reset():
    save_data(deepcopy(DEFAULT_DATA))
    return jsonify({"success": True, "message": "設定をリセットしました"})


# =============================================================================
# シフト保存・管理
# =============================================================================

@api_bp.route('/shifts', methods=['GET'])
@login_required
def api_list_shifts():
    shifts = list_shifts()
    return jsonify(shifts)


@api_bp.route('/shifts/<int:year>/<int:month>', methods=['GET'])
@login_required
def api_get_shift(year, month):
    shift = load_shift(year, month)
    if shift:
        return jsonify(shift)
    return jsonify({"error": "シフトが見つかりません"}), 404


@api_bp.route('/shifts/<int:year>/<int:month>', methods=['POST'])
@login_required
def api_save_shift(year, month):
    data = request.json
    shift_data = data.get('shift_data', {})
    staff_counts = data.get('staff_counts', {})
    ng_days_data = data.get('ng_days', {})
    exceptions_data = data.get('exceptions', {})

    success = save_shift(year, month, shift_data, staff_counts, ng_days_data, exceptions_data)
    if success:
        return jsonify({"success": True, "message": f"{year}年{month}月のシフトを保存しました"})
    return jsonify({"error": "シフトの保存に失敗しました"}), 500


@api_bp.route('/shifts/<int:year>/<int:month>', methods=['DELETE'])
@login_required
def api_delete_shift(year, month):
    success = delete_shift(year, month)
    if success:
        return jsonify({"success": True, "message": f"{year}年{month}月のシフトを削除しました"})
    return jsonify({"error": "シフトの削除に失敗しました"}), 500


# =============================================================================
# カレンダー・シフト生成
# =============================================================================

@api_bp.route('/calendar/<int:year>/<int:month>', methods=['GET'])
@login_required
def api_get_calendar(year, month):
    cal_data = get_calendar_data(year, month)
    return jsonify(cal_data)


@api_bp.route('/generate_shift', methods=['POST'])
@login_required
def api_generate_shift():
    data = request.json
    year = data.get('year', datetime.now().year)
    month = data.get('month', datetime.now().month)
    ng_days_data = data.get('ng_days', get_ng_days())
    month_exceptions = data.get('exceptions', {})

    exceptions = get_exceptions()
    key = f"{year}-{month:02d}"
    exceptions[key] = month_exceptions
    set_exceptions(exceptions)

    result = generate_shift(year, month, ng_days_data, month_exceptions)
    return jsonify(result)


# =============================================================================
# エクスポート
# =============================================================================

@api_bp.route('/export_excel', methods=['POST'])
@login_required
def api_export_excel():
    data = request.json
    year = data.get('year', datetime.now().year)
    month = data.get('month', datetime.now().month)
    month_exceptions = data.get('exceptions', {})

    shift_data = data.get('shift_data')
    if not shift_data:
        ng_days_data = data.get('ng_days', get_ng_days())
        result = generate_shift(year, month, ng_days_data, month_exceptions)
        shift_data = result['shift']

    wb = create_excel_shift(year, month, shift_data, month_exceptions)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"shift_{year}_{month:02d}.xlsx"

    response = send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@api_bp.route('/export_pdf', methods=['POST'])
@login_required
def api_export_pdf():
    data = request.json
    year = data.get('year', datetime.now().year)
    month = data.get('month', datetime.now().month)
    month_exceptions = data.get('exceptions', {})

    shift_data = data.get('shift_data')
    if not shift_data:
        ng_days_data = data.get('ng_days', get_ng_days())
        result = generate_shift(year, month, ng_days_data, month_exceptions)
        shift_data = result['shift']

    output = create_pdf_shift(year, month, shift_data, month_exceptions)

    filename = f"shift_{year}_{month:02d}.pdf"

    response = send_file(
        output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache'
    return response
