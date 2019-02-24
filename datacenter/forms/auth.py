# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, EqualTo, Regexp

from datacenter.models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('下次自动登陆')
    submit = SubmitField('登陆')


class RegisterForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(1, 30)],
                       render_kw={'placeholder': '你的真实姓名'},
                       # description='你的真实姓名',
                       )
    # email = StringField('邮箱', validators=[DataRequired(), Length(1, 254), Email()])
    username = StringField('用户名', render_kw={'placeholder': '将作为个人文件夹名'},
                           validators=[DataRequired(), Length(1, 20),
                                       Regexp('^[a-zA-Z0-9]*$',
                                              message='用户名只能包含 a-z, A-Z , 0-9.')])
    password = PasswordField('密码', render_kw={'placeholder': '3个字符以上'},
                             validators=[
                                 DataRequired(), Length(3, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码', render_kw={'placeholder': '3个字符以上'},
                              validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已经被注册.')


