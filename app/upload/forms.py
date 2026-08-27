from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from wtforms.widgets import HiddenInput


class DocumentUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    document_type = SelectField('Document Type', choices=[
        ('essay', 'Essay'),
        ('handout', 'Handout')
    ], validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload Document')


class ExamPaperUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    year = StringField('Year', validators=[Length(max=50)])
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload Exam Paper')
