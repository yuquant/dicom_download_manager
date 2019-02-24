# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask import render_template, jsonify, Blueprint
from flask_login import current_user
from sqlalchemy import and_
from datacenter.models import Tasks, Patients
ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/notifications-count')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    count1 = Tasks.query.filter(Tasks.status_id == 6).order_by(Tasks.priority.desc()).order_by(
        Tasks.timestamp).count()
    # count2 = User.query.filter(User.locked == 1).count()
    # count = count1 + count2
    # print(count2)
    # print(count)
    # count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count1)


@ajax_bp.route('/bar/', methods=['GET'])
def bar():
    """
    传输进度,临时采用查表统计,想提升性能可通过redis记录
    :return:
    """
    task = Tasks.query.filter(and_(Tasks.active, Tasks.status_id == 7)).order_by(
        Tasks.timestamp.desc()).first()
    ret = {'title': '', 'percent': '0'}
    if task:
        finished_count = Patients.query.filter(and_(Patients.task_id == task.id, Patients.status_id != 7)).count()
        count = Patients.query.filter(Patients.task_id == task.id).count()
        ratio = str(finished_count/count*100)
        ret = {'title': task.title, 'percent': ratio}
    # ret = {'title': 'biaoti', 'percent': '20'}
    # print(ret)
    return jsonify(ret)
