# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""
import os
import time
from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint, jsonify
from flask_login import login_required, current_user, logout_user
from sqlalchemy.sql.expression import func

from datacenter.decorators import confirm_required, permission_required
from datacenter.extensions import db
from datacenter.forms.main import DescriptionForm, TagForm, CommentForm, \
    ResearchForm
from datacenter.models import User, Photo, Tag, Follow, Collect, Comment, Notification, \
    Tasks, StatusDict, AEDict, Patients
from datacenter.notifications import push_comment_notification, push_collect_notification
from datacenter.utils import rename_image, resize_image, redirect_back, flash_errors, \
    random_filename

main_bp = Blueprint('main', __name__)


def insert_form(form):
    """
    提交表单后插入数据库
    :param form:
    :return:
    """
    assert isinstance(form, ResearchForm)
    res = form.data
    # f = request.files.get('patients')
    f = form.other_file.data
    if not res['folder_name']:
        timestring = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        res['folder_name'] = '{timestamp}-{title}-{researcher}'.format(timestamp=timestring,
                                                                       title=res['title'],
                                                                       researcher=res['researcher'])
    res['folder_name'] = os.path.join('downloads', current_user.username, res['folder_name'].replace(' ', ''))
    if f:
        # 存储到下载处
        output_dir = res['folder_name']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        f.save(os.path.join(output_dir, f.filename))
        # 保存文件到数据库
        filename = random_filename(f.filename)
        file_path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
        f.save(file_path)
        res['other_file'] = filename
    lines = res['patients'].split('\r\n')
    patients = [line for line in lines if line.strip() != '']
    res.pop('patients')
    res.pop('submit')
    res.pop('csrf_token')
    if current_user.can('MODERATE'):
        res['status_id'] = 7
    # 一对多关系插入，参数传入一的一方
    patients_obj = []
    patient_status_id = StatusDict.query.filter(StatusDict.status_name == '队列中').first_or_404().id

    for patient in patients:
        patients_obj.append(Patients(accession_no=patient, status_id=patient_status_id))
    task = Tasks(**res, patients=patients_obj, patients_count=len(patients_obj), researcher_id=current_user.id)
    db.session.add(task)
    db.session.add_all(patients_obj)
    db.session.commit()


# @main_bp.route('/')
# def index():
#     if current_user.is_authenticated:
#         page = request.args.get('page', 1, type=int)
#         per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
#         pagination = Photo.query \
#             .join(Follow, Follow.followed_id == Photo.author_id) \
#             .filter(Follow.follower_id == current_user.id) \
#             .order_by(Photo.timestamp.desc()) \
#             .paginate(page, per_page)
#         photos = pagination.items
#     else:
#         pagination = None
#         photos = None
#     tags = Tag.query.join(Tag.photos).group_by(Tag.id).order_by(func.count(Photo.id).desc()).limit(10)
#     return render_template('main/index.html', pagination=pagination, photos=photos, tags=tags, Collect=Collect)


@main_bp.route('/task/', methods=['GET', 'POST'])
def index():
    """
    任务提交页面
    """
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        if user == current_user and user.locked:
            # flash('您的账户尚未激活,请联系管理员激活.', 'danger')
            return redirect(url_for('user.index', username=current_user.username))
        # if user == current_user and not user.active:
        #     logout_user()

        form = ResearchForm()
        if form.validate_on_submit():
            # title = form.title.data
            # researcher = form.researcher.data
            insert_form(form)
            # flash('提交成功')
            return redirect(url_for('.tasks'))
    else:
        form = None
        user = None
    return render_template('main/task.html', form=form, user=user)


@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def percent():
    """
    任务进度
    :return:
    """
    page = request.args.get('page', 1, type=int)
    pagination = Tasks.query.filter(Tasks.status_id == 7).order_by(Tasks.priority.desc()).order_by(
        Tasks.timestamp).paginate(page,
                                  per_page=current_app.config['TASK_PER_PAGE'],
                                  # per_page=5,
                                  )
    # waiting_tasks = with_dict(pagination)
    waiting_tasks = pagination.items
    return render_template('main/percent.html', tasks=waiting_tasks, pagination=pagination)


@main_bp.route('/explore')
def explore():
    photos = Photo.query.order_by(func.random()).limit(12)
    return render_template('main/explore.html', photos=photos)


@main_bp.route('/show/<int:uid>', methods=['GET'])
def show(uid):
    task = Tasks.query.filter_by(id=uid).first_or_404()
    return render_template('main/show.html', task=task)


@main_bp.route('/tasks/', methods=['GET'])
@login_required
def tasks():
    """
    所有任务列表（分页显示）
    :return:
    """
    page = request.args.get('page', 1, type=int)
    pagination = Tasks.query.order_by(Tasks.timestamp.desc()).paginate(page,
                                                                       per_page=current_app.config['TASK_PER_PAGE'])
    posts = pagination.items
    return render_template('main/tasks.html', pagination=pagination, tasks=posts)


@main_bp.route('/status/<int:uid>', methods=['GET'])
@login_required
def status(uid):
    patients = Patients.query.filter_by(task_id=uid).all()
    return render_template('main/status.html', patients=patients)


@main_bp.route('/edit/<int:uid>', methods=['GET', 'POST'])
def edit(uid):
    """
    编辑任务
    :param uid:
    :return:
    """
    if current_user.is_authenticated:
        user = User.query.filter_by(username=current_user.username).first_or_404()
        if user == current_user and user.locked:
            # flash('您的账户尚未激活,请联系管理员激活.', 'danger')
            return redirect(url_for('user.index', username=current_user.username))

        form = ResearchForm()

        if request.method == 'GET':
            # task = Tasks.query.filter_by(id=uid).first_or_404()
            # 通过主键获取
            task = Tasks.query.get_or_404(uid)
            patients = task.patients
            form.title.data = task.title
            form.patients.data = '\r\n'.join([patient.accession_no for patient in patients])
            form.transport_id.data = task.transport_id
            form.series.data = task.series
            form.time_wait.data = task.time_wait
            form.research_plan.data = task.research_plan
            form.folder_name.data = task.folder_name
            return render_template('main/task.html', form=form, user=user)
        if request.method == 'POST':
            if form.validate_on_submit():
                insert_form(form)
                # flash('提交成功')
                return redirect(url_for('.tasks'))
    else:
        return redirect(url_for('auth.login'))


# @main_bp.route('/search')
# def search():
#     q = request.args.get('q', '')
#     if q == '':
#         flash('Enter keyword about photo, user or tag.', 'warning')
#         return redirect_back()
#
#     category = request.args.get('category', 'photo')
#     page = request.args.get('page', 1, type=int)
#     per_page = current_app.config['ALBUMY_SEARCH_RESULT_PER_PAGE']
#     if category == 'user':
#         pagination = User.query.whooshee_search(q).paginate(page, per_page)
#     elif category == 'tag':
#         pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
#     else:
#         pagination = Photo.query.whooshee_search(q).paginate(page, per_page)
#     results = pagination.items
#     return render_template('main/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '')
    if q == '':
        flash('Enter keyword about photo, user or tag.', 'warning')
        return redirect_back()

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['TASK_PER_PAGE']
    pagination = Tasks.query.whooshee_search(q).paginate(page, per_page)
    tasks = pagination.items
    return render_template('main/search.html', q=q, tasks=tasks, pagination=pagination)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['ALBUMY_UPLOAD_PATH'], filename)


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = rename_image(f.filename)
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))
        filename_s = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['small'])
        filename_m = resize_image(f, filename, current_app.config['ALBUMY_PHOTO_SIZE']['medium'])
        photo = Photo(
            filename=filename,
            filename_s=filename_s,
            filename_m=filename_m,
            author=current_user._get_current_object()
        )
        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')


@main_bp.route('/photo/<int:photo_id>')
def show_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(photo).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = photo.description
    return render_template('main/photo.html', photo=photo, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)


@main_bp.route('/photo/n/<int:photo_id>')
def photo_next(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()

    if photo_n is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/photo/p/<int:photo_id>')
def photo_previous(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()

    if photo_p is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))
    return redirect(url_for('.show_photo', photo_id=photo_p.id))


@main_bp.route('/collect/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.collect(photo)
    flash('Photo collected.', 'success')
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
@login_required
def uncollect(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_photo', photo_id=photo_id))

    current_user.uncollect(photo)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('Comment reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/photo/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash('Photo reported.', 'success')
    return redirect(url_for('.show_photo', photo_id=photo.id))


@main_bp.route('/photo/<int:photo_id>/collectors')
def show_collectors(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, photo=photo, pagination=pagination)


@main_bp.route('/photo/<int:photo_id>/description', methods=['POST'])
@login_required
def edit_description(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        photo.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/photo/<int:photo_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, photo=photo)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_comment_notification(photo_id=photo.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != photo.author and photo.author.receive_comment_notification:
            push_comment_notification(photo_id, receiver=photo.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id, page=page))


@main_bp.route('/photo/<int:photo_id>/tag/new', methods=['POST'])
@login_required
def new_tag(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in photo.tags:
                photo.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/set-comment/<int:photo_id>', methods=['POST'])
@login_required
def set_comment(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author:
        abort(403)

    if photo.can_comment:
        photo.can_comment = False
        flash('Comment disabled', 'info')
    else:
        photo.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    return redirect(url_for('.show_photo', photo_id=photo_id))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_photo', photo_id=comment.photo_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted.', 'info')

    photo_n = Photo.query.with_parent(photo.author).filter(Photo.id < photo_id).order_by(Photo.id.desc()).first()
    if photo_n is None:
        photo_p = Photo.query.with_parent(photo.author).filter(Photo.id > photo_id).order_by(Photo.id.asc()).first()
        if photo_p is None:
            return redirect(url_for('user.index', username=photo.author.username))
        return redirect(url_for('.show_photo', photo_id=photo_p.id))
    return redirect(url_for('.show_photo', photo_id=photo_n.id))


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.photo.author \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Photo.query.with_parent(tag).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collects':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('main/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@main_bp.route('/delete/tag/<int:photo_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(photo_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Photo.query.get_or_404(photo_id)
    if current_user != photo.author and not current_user.can('MODERATE'):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', photo_id=photo_id))
