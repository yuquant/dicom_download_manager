# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask import render_template, flash, redirect, url_for, current_app, request, Blueprint
from flask_login import login_required, current_user, fresh_login_required
from sqlalchemy import and_

from datacenter.extensions import db, avatars
from datacenter.forms.user import EditProfileForm, UploadAvatarForm, CropAvatarForm, \
    ChangePasswordForm, DeleteAccountForm
from datacenter.models import User, Tasks
from datacenter.utils import redirect_back, flash_errors

user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user and user.locked:
        flash('您的账户尚未激活,请修改资料并联系管理员激活账户', 'danger')
    # if user == current_user and not user.active:
    #     logout_user()

    page = request.args.get('page', 1, type=int)
    pagination = Tasks.query.filter(and_(Tasks.researcher_id == current_user.id, Tasks.status_id.in_([6, 7]))).order_by(
        Tasks.timestamp).paginate(page,
                                  per_page=current_app.config['TASK_PER_PAGE'],
                                  )
    posts = pagination.items
    return render_template('user/mytasks.html', user=user, pagination=pagination, tasks=posts)


@user_bp.route('/<username>/finished')
def finished(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Tasks.query.filter(and_(Tasks.researcher_id == current_user.id, Tasks.status_id.notin_([6, 7]))).order_by(Tasks.priority.desc()).order_by(
        Tasks.timestamp).paginate(page,
                                  per_page=current_app.config['TASK_PER_PAGE'],
                                  )
    posts = pagination.items
    return render_template('user/mytask_finished.html', user=user, pagination=pagination, tasks=posts)


@user_bp.route('/cancel/<int:task_id>', methods=['GET', 'POST'])
@login_required
def cancel(task_id):
    task = Tasks.query.get_or_404(task_id)
    # if task.status_id == 7:  # 队列中任务
    task.status_id = 2  # 取消
    db.session.commit()
    return redirect_back()


@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        # current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
        # flash('Profile updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    # form.website.data = current_user.website
    form.location.data = current_user.location
    return render_template('user/settings/edit_profile.html', form=form)


@user_bp.route('/settings/avatar')
@login_required
# @confirm_required
def change_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form, crop_form=crop_form)


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
# @confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('Image uploaded, please crop.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
# @confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        db.session.commit()
        flash('Avatar updated.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/change-password', methods=['GET', 'POST'])
@fresh_login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.validate_password(form.old_password.data):
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Password updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_password.html', form=form)


@user_bp.route('/settings/account/delete', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('Your are free, goodbye!', 'success')
        return redirect(url_for('main.index'))
    return render_template('user/settings/delete_account.html', form=form)
