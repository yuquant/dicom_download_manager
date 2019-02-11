# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask import render_template, jsonify, Blueprint
from flask_login import current_user
from sqlalchemy import and_
from datacenter.models import User, Photo, Notification, Tasks, Patients
from datacenter.notifications import push_collect_notification, push_follow_notification
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


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1  # minus user self
    return jsonify(count=count)


@ajax_bp.route('/<int:photo_id>/followers-count')
def collectors_count(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    count = len(photo.collectors)
    return jsonify(count=count)


@ajax_bp.route('/collect/<int:photo_id>', methods=['POST'])
def collect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('COLLECT'):
        return jsonify(message='No permission.'), 403

    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        return jsonify(message='Already collected.'), 400

    current_user.collect(photo)
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return jsonify(message='Photo collected.')


@ajax_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
def uncollect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        return jsonify(message='Not collect yet.'), 400

    current_user.uncollect(photo)
    return jsonify(message='Collect canceled.')


@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('FOLLOW'):
        return jsonify(message='No permission.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='Already followed.'), 400

    current_user.follow(user)
    if user.receive_collect_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return jsonify(message='User followed.')


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='Not follow yet.'), 400

    current_user.unfollow(user)
    return jsonify(message='Follow canceled.')


@ajax_bp.route('/bar/', methods=['GET'])
def bar():
    """
    传输进度,临时采用查表统计,想提升性能可通过redis记录
    :return:
    """
    task = Tasks.query.filter(Tasks.active).order_by(
        Tasks.timestamp.desc()).first()
    ret = {'title': '', 'percent': '0'}
    if task:
        finished_count = Patients.query.filter(and_(Patients.task_id == task.id, Patients.status_id != 7)).count()
        count = Patients.query.filter(Patients.task_id == task.id).count()
        ratio = str(finished_count/count*100)
        ret = {'title': task.title, 'percent': ratio}
    # ret = {'title': 'biaoti', 'percent': '20'}
    # ret = app.config['BAR']
    print(ret)
    return jsonify(ret)