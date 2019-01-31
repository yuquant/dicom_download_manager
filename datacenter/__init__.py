# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
import os

import click
from flask import Flask, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from datacenter.blueprints.admin import admin_bp
from datacenter.blueprints.ajax import ajax_bp
from datacenter.blueprints.auth import auth_bp
from datacenter.blueprints.main import main_bp
from datacenter.blueprints.user import user_bp
from datacenter.extensions import bootstrap, db, login_manager, mail, dropzone, moment, whooshee, avatars, csrf, ckeditor
from datacenter.models import Role, User, Photo, Tag, Follow, Notification, Comment, Collect, Permission
from datacenter.models import Tasks, StatusDict, AEDict
from datacenter.settings import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('datacenter')
    
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    dropzone.init_app(app)
    moment.init_app(app)
    whooshee.init_app(app)
    avatars.init_app(app)
    csrf.init_app(app)
    ckeditor.init_app(app)


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Photo=Photo, Tag=Tag,
                    Follow=Follow, Collect=Collect, Comment=Comment,
                    Notification=Notification)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    def init():
        """Initialize Albumy."""
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')

    @app.cli.command()
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows, default is 50.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 500.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 500.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 500.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 500.')
    def forge(user, follow, photo, tag, collect, comment):
        """Generate fake data."""

        from datacenter.fakes import fake_admin, fake_comment, fake_follow, fake_photo, fake_tag, fake_user, fake_collect

        db.drop_all()
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()
        click.echo('Generating the administrator...')
        fake_admin()
        click.echo('Generating %d users...' % user)
        fake_user(user)
        click.echo('Generating %d follows...' % follow)
        fake_follow(follow)
        click.echo('Generating %d tags...' % tag)
        fake_tag(tag)
        click.echo('Generating %d photos...' % photo)
        fake_photo(photo)
        click.echo('Generating %d collects...' % photo)
        fake_collect(collect)
        click.echo('Generating %d comments...' % comment)
        fake_comment(comment)
        click.echo('Done.')

    @app.cli.command()
    def initdict():
        """初始化状态字典"""
        # StatusDict.__table__.drop()
        status_dict = {0: '待处理', 1: '完成', 2: '取消', 3: '失败', 4: '部分完成', 5: '未知错误'}
        status_obj = []
        for key, val in status_dict.items():
            status_obj.append(StatusDict(status_id=key, status_name=val))
        db.session.add_all(status_obj)
        db.session.commit()
        click.echo('Initialized status dict.')

    @app.cli.command()
    def initaedict():
        """初始化AE列表"""
        ae_list = [
            ['DOWNLOAD', '下载', 0],
            ['SMIT_Q', '新网PACS', 1],
            ['ISDPHILIPS', '飞利浦ISD', 2]
                   ]
        ae_obj = []
        for ae_title, ae_name, ae_id in ae_list:
            ae_obj.append(AEDict(ae_title=ae_title, ae_name=ae_name, ae_id=ae_id))
        db.session.add_all(ae_obj)
        db.session.commit()
        click.echo('Initialized ae dict.')
