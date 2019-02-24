# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask import render_template, flash, Blueprint, request, current_app
from flask_login import login_required

from datacenter.decorators import admin_required, permission_required
from datacenter.extensions import db
from datacenter.forms.admin import EditProfileAdminForm
from datacenter.models import Role, User,Tasks
from datacenter.utils import redirect_back

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        role = Role.query.get(form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.bio = form.bio.data
        # user.website = form.website.data
        # user.confirmed = form.confirmed.data
        # user.active = form.active.data
        user.location = form.location.data
        user.username = form.username.data
        # user.email = form.email.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect_back()
    form.name.data = user.name
    form.role.data = user.role_id
    form.bio.data = user.bio
    # form.website.data = user.website
    form.location.data = user.location
    form.username.data = user.username
    # form.email.data = user.email
    # form.confirmed.data = user.confirmed
    # form.active.data = user.active
    return render_template('admin/edit_profile.html', form=form, user=user)


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.block()
    flash('Account blocked.', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('Block canceled.', 'info')
    return redirect_back()


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('Account locked.', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('Lock canceled.', 'info')
    return redirect_back()


@admin_bp.route('/to_top/<int:task_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def to_top(task_id):
    # 队列中任务优先级最高的
    current_priority_task = Tasks.query.filter(Tasks.status_id == 7).order_by(Tasks.priority.desc()).first_or_404()
    task = Tasks.query.get_or_404(task_id)
    task.priority = current_priority_task.priority + 1
    db.session.commit()
    # flash('{}任务已置顶'.format(task.title))
    # return redirect(url_for('.percent'))
    return redirect_back()


@admin_bp.route('/cancel/<int:task_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def cancel(task_id):
    task = Tasks.query.get_or_404(task_id)
    if task.status_id == 7:  # 队列中任务
        task.status_id = 2  # 取消
        db.session.commit()
    return redirect_back()


@admin_bp.route('/accept/<int:task_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def accept(task_id):
    task = Tasks.query.get_or_404(task_id)
    print(task.status_id)
    if task.status_id == 6:  # 待审批任务
        task.status_id = 7  # 接受
        # print('accept')
        db.session.commit()
    return redirect_back()


@admin_bp.route('/reject/<int:task_id>', methods=['GET', 'POST'])
@login_required
@permission_required('MODERATE')
def reject(task_id):
    task = Tasks.query.get_or_404(task_id)
    if task.status_id == 6:
        task.status_id = 8  # 拒绝
        db.session.commit()
    return redirect_back()


@admin_bp.route('/manage/user')
@login_required
@permission_required('ADMINISTER')
def manage_user():
    filter_rule = request.args.get('filter', 'all')  # 'all', 'locked', 'blocked', 'administrator', 'moderator'
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['MANAGE_USER_PER_PAGE']
    administrator = Role.query.filter_by(name='Administrator').first()
    moderator = Role.query.filter_by(name='Moderator').first()

    if filter_rule == 'locked':
        filtered_users = User.query.filter_by(locked=True)
    elif filter_rule == 'blocked':
        filtered_users = User.query.filter_by(locked=False)
    elif filter_rule == 'administrator':
        filtered_users = User.query.filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filtered_users = User.query.filter_by(role=moderator)
    else:
        filtered_users = User.query

    pagination = filtered_users.order_by(User.member_since.desc()).paginate(page, per_page)
    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)


@admin_bp.route('/')
@admin_bp.route('/manage/task')
@login_required
@permission_required('MODERATE')
def manage_task():
    page = request.args.get('page', 1, type=int)
    # 待审批任务
    pagination = Tasks.query.filter(Tasks.status_id == 6).order_by(Tasks.priority.desc()).order_by(
        Tasks.timestamp).paginate(page,
                                  per_page=current_app.config['TASK_PER_PAGE'],
                                  )
    # waiting_tasks = with_dict(pagination)
    tasks = pagination.items
    return render_template('admin/manage_task.html', pagination=pagination, tasks=tasks)

