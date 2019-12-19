# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description : 
"""
import os
import time
from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, Blueprint
from flask_login import login_required, current_user
from datacenter.extensions import db
from datacenter.forms.main import ResearchForm
from datacenter.models import User, Tasks, StatusDict, Patients
from datacenter.utils import redirect_back, random_filename

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
        res['folder_name'] = '{title}'.format(title=res['title'])

        # res['folder_name'] = '{timestamp}-{title}-{researcher}'.format(timestamp=timestring,
        #                                                                title=res['title'],
        #                                                                researcher=res['researcher'])

    res['folder_name'] = res['folder_name'].replace(' ', '')
    if f:
        # 存储到下载处 TODO:通过配置文件实现
        # output_dir = os.path.join('downloads', current_user.username, res['folder_name'].replace(' ', ''))
        output_dir = os.path.join('downloads', current_user.username, 'data', res['folder_name'])

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


@main_bp.route('/', methods=['GET', 'POST'])
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


@main_bp.route('/percent', methods=['GET', 'POST'])
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


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

