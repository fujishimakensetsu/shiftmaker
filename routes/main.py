# -*- coding: utf-8 -*-
"""
メインページルーティング
"""

from flask import Blueprint, render_template
from flask_login import login_required

from models import get_locations, get_staff

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    return render_template('index.html',
                         locations=get_locations(),
                         staff=get_staff())


@main_bp.route('/locations')
@login_required
def locations_page():
    return render_template('locations.html', locations=get_locations())


@main_bp.route('/staff')
@login_required
def staff_page():
    return render_template('staff.html', staff=get_staff(), locations=get_locations())


@main_bp.route('/system')
@login_required
def system_page():
    return render_template('system.html')
