# -*- coding: utf-8 -*-
"""
PDF出力サービス
"""

import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from models import get_locations, get_staff
from .calendar_service import get_calendar_data


def get_japanese_font():
    """日本語フォントを取得"""
    font_paths = [
        # Linux (Docker/Cloud Run) - IPA fonts
        '/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf',
        '/usr/share/fonts/truetype/ipaexfont-gothic/ipaexg.ttf',
        '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
        '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
        # Linux - Noto fonts
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        # Windows fonts
        'C:/Windows/Fonts/msgothic.ttc',
        'C:/Windows/Fonts/meiryo.ttc',
        'C:/Windows/Fonts/YuGothM.ttc',
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    return None


def create_pdf_shift(year, month, shift_data, month_exceptions):
    """PDF形式のシフト表を作成"""
    locations = get_locations()
    staff_list = get_staff()
    staff_dict = {s['id']: s['name'] for s in staff_list}
    cal_data = get_calendar_data(year, month, month_exceptions)
    num_locations = len(locations)

    output = BytesIO()
    page_width, page_height = landscape(A4)

    c = canvas.Canvas(output, pagesize=landscape(A4))

    # 日本語フォント登録
    font_path = get_japanese_font()
    font_name = 'Helvetica'
    font_name_bold = 'Helvetica-Bold'
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
            font_name = 'JapaneseFont'
            bold_paths = [
                # Linux (Docker/Cloud Run) - IPA fonts (use same as regular)
                '/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf',
                '/usr/share/fonts/truetype/ipaexfont-gothic/ipaexg.ttf',
                '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
                # Windows fonts
                'C:/Windows/Fonts/meiryob.ttc',
                'C:/Windows/Fonts/YuGothB.ttc',
                'C:/Windows/Fonts/msgothic.ttc',
            ]
            font_name_bold = font_name
            for bold_path in bold_paths:
                if os.path.exists(bold_path):
                    try:
                        pdfmetrics.registerFont(TTFont('JapaneseFontBold', bold_path))
                        font_name_bold = 'JapaneseFontBold'
                        break
                    except:
                        pass
        except:
            font_name = 'Helvetica'
            font_name_bold = 'Helvetica-Bold'

    # カレンダーデータを週単位でグループ化
    weeks = []
    current_week = [None] * 7
    for day_info in cal_data:
        weekday_jp = (day_info['weekday'] + 1) % 7
        current_week[weekday_jp] = day_info
        if weekday_jp == 6:
            weeks.append(current_week)
            current_week = [None] * 7
    if any(d is not None for d in current_week):
        weeks.append(current_week)

    # レイアウト計算
    margin = 10
    table_x = margin
    table_y = margin
    table_width = page_width - 2 * margin
    table_height = page_height - 2 * margin

    first_col_width = 40
    other_col_width = (table_width - first_col_width) / 7
    col_widths = [first_col_width] + [other_col_width] * 7

    num_rows = 1 + len(weeks) * (1 + num_locations)
    row_height = table_height / num_rows
    font_size = min(10, row_height * 0.7)

    weekday_headers = ['', '日', '月', '火', '水', '木', '金', '土']

    def get_col_x(col_idx):
        x = table_x
        for i in range(col_idx):
            x += col_widths[i]
        return x

    def draw_cell(row_idx, col_idx, text, bg_color=None, text_color=None, bold=False, row_span=1):
        x = get_col_x(col_idx)
        y = page_height - table_y - (row_idx + row_span) * row_height
        w = col_widths[col_idx]
        h = row_height * row_span

        if bg_color:
            c.setFillColor(bg_color)
            c.rect(x, y, w, h, fill=1, stroke=0)

        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h, fill=0, stroke=1)

        if text:
            use_font = font_name_bold if bold else font_name
            c.setFont(use_font, font_size)
            if text_color:
                c.setFillColor(text_color)
            else:
                c.setFillColor(colors.black)
            text_width = c.stringWidth(str(text), use_font, font_size)
            text_x = x + (w - text_width) / 2
            text_y = y + (h - font_size) / 2 + font_size * 0.2
            c.drawString(text_x, text_y, str(text))

    # ヘッダー行
    for col_idx, header in enumerate(weekday_headers):
        if col_idx == 0:
            bg = colors.HexColor('#4472C4')
        elif col_idx == 1:
            bg = colors.HexColor('#dc3545')
        elif col_idx == 7:
            bg = colors.HexColor('#0d6efd')
        else:
            bg = colors.HexColor('#4472C4')
        draw_cell(0, col_idx, header, bg_color=bg, text_color=colors.white)

    # データ行
    current_row = 1
    for week_idx, week in enumerate(weeks):
        all_closed_days = []
        for day_info in week:
            if day_info:
                all_closed = all(loc_info.get('is_closed_day', False) for loc_info in day_info['locations'])
                all_closed_days.append(all_closed)
            else:
                all_closed_days.append(False)

        month_text = f"{month}月" if week_idx == 0 else ""
        draw_cell(current_row, 0, month_text, bg_color=colors.HexColor('#f8f9fa'))

        for col_idx, day_info in enumerate(week):
            col = col_idx + 1
            if day_info:
                day = day_info['day']
                weekday_jp = (day_info['weekday'] + 1) % 7
                is_holiday = day_info.get('is_holiday', False)
                holiday_name = day_info.get('holiday_name', '')

                cell_text = str(day)
                if is_holiday and holiday_name:
                    cell_text = f"{day} {holiday_name}"

                if is_holiday or weekday_jp == 0:
                    bg = colors.HexColor('#ffe6e6')
                    txt_color = colors.HexColor('#dc3545')
                elif weekday_jp == 6:
                    bg = colors.HexColor('#e6f0ff')
                    txt_color = colors.HexColor('#0d6efd')
                else:
                    bg = None
                    txt_color = colors.black
                draw_cell(current_row, col, cell_text, bg_color=bg, text_color=txt_color)
            else:
                draw_cell(current_row, col, "")
        current_row += 1

        first_loc_row = current_row
        for col_idx, day_info in enumerate(week):
            col = col_idx + 1
            if day_info and all_closed_days[col_idx]:
                draw_cell(first_loc_row, col, "定休日",
                         bg_color=colors.HexColor('#f0f0f0'),
                         row_span=num_locations)

        for loc_idx, loc in enumerate(locations):
            draw_cell(current_row, 0, loc['name'], bg_color=colors.HexColor('#f8f9fa'))

            for col_idx, day_info in enumerate(week):
                col = col_idx + 1
                if all_closed_days[col_idx]:
                    continue

                if day_info:
                    loc_info = next((l for l in day_info['locations'] if l['id'] == loc['id']), None)
                    bg = None
                    is_name = False

                    if loc_info and loc_info.get('is_closed_day', False):
                        cell_text = "休"
                        bg = colors.HexColor('#f0f0f0')
                    elif loc_info and not loc_info['is_working']:
                        cell_text = "休"
                    else:
                        assigned_ids = shift_data.get(day_info['date'], {}).get(str(loc['id']), [])
                        if assigned_ids:
                            names = [staff_dict.get(int(sid) if isinstance(sid, str) else sid, '?')
                                   for sid in assigned_ids if sid]
                            cell_text = "/".join(names) if names else "-"
                            is_name = bool(names)
                        else:
                            cell_text = "-"

                    draw_cell(current_row, col, cell_text, bg_color=bg, bold=is_name)
                else:
                    draw_cell(current_row, col, "")
            current_row += 1

    c.save()
    output.seek(0)
    return output
