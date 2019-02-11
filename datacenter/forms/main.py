# -*- coding: utf-8 -*-
"""
Author : Jason
Github : https://github.com/yuquant
Description :
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, Regexp

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
    title = StringField('研究题目*', validators=[DataRequired(), Length(1, 50)],
                        render_kw={'placeholder': '必填', 'class': 'add-on'},
                        )
    patients = TextAreaField('检查号列表*', validators=[DataRequired()],
                             render_kw={'placeholder': '必填,换行符隔开', 'title': '必填,换行符隔开'},)

    transport_id = SelectField('DICOM图像传输*', coerce=int, choices='', validators=[InputRequired()])

    folder_name = StringField('下载后的文件夹命名',
                              validators=[Length(0, 50)],
                              render_kw={'placeholder': '不修改则按照默认规则命名', 'title': '不修改则按照默认规则命名'},)
    time_wait = FloatField('传输间隔（分钟）', default=5, validators=[NumberRange(0, 20)])
    series = StringField('序列描述',
                         render_kw={'placeholder': '不填代表全部序列;谨慎填写,填写时用英文逗号隔开可能的序列描述',
                                    'title': '不填代表全部序列;谨慎填写,填写时用英文逗号隔开可能的序列描述'},)
    other_file = FileField('其他相关文件')
    research_plan = CKEditorField('研究说明',
                                  render_kw={'placeholder': '可复制doc文档到此处', 'title': '可复制doc文档到此处'},)
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport_id.choices = [(a.id, a.ae_name) for a in AEDict.query.all()]