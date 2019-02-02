# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length

from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
# from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, FileField, IntegerField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, InputRequired, NumberRange
from datacenter.models import AEDict
# from run import app
# from datacenter.extensions import db
# from datacenter import create_app


class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField('Add Tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()


class CommentForm(FlaskForm):
    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField()


class ResearchForm(FlaskForm):
    title = StringField('1.研究题目（*必填）', validators=[DataRequired(), Length(1, 50)])
    # researcher = StringField('2.研究者（*必填）', validators=[DataRequired(), Length(1, 20)])
    patients = TextAreaField('3.检查号列表(*必填)', validators=[DataRequired()])
    transport_to = SelectField('4.DICOM图像传输（*必填）', coerce=int, choices='', validators=[InputRequired()])
    folder_name = StringField('&nbsp&nbsp下载后的文件夹命名（不修改则按照默认规则命名）',
                              validators=[Length(0, 50)])
    series = StringField('5.序列描述（多个可能的序列用逗号分隔开）')
    time_wait = FloatField('6.图像传输时间间隔（分钟）', default=5, validators=[NumberRange(0, 20)])
    research_plan = CKEditorField('7.研究说明（可复制doc文档到此处）')
    other_file = FileField('8.其他相关文件')
    # anonymous = BooleanField('是否匿名为Nifty', default=0)
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport_to.choices = [(a.ae_id, a.ae_name) for a in AEDict.query.all()]