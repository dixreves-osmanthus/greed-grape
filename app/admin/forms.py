from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Email, Optional


class CategoryForm(FlaskForm):
    """Form for question categories."""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    level = SelectField('Level', choices=[
        ('high_school', 'High School'),
        ('university', 'University')
    ], validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save')


class DocumentCategoryForm(FlaskForm):
    """Form for document categories."""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    level = SelectField('Level', choices=[
        ('high_school', 'High School'),
        ('university', 'University')
    ], validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    document_type = SelectField('Document Type', choices=[
        ('essay', 'Essay'),
        ('handout', 'Handout')
    ], validators=[DataRequired()])
    submit = SubmitField('Save')


class QuestionForm(FlaskForm):
    """Form for questions."""
    content = TextAreaField('Question Content', validators=[DataRequired()])
    option_a = StringField('Option A')
    option_b = StringField('Option B')
    option_c = StringField('Option C')
    option_d = StringField('Option D')
    correct_answer = SelectField('Correct Answer', choices=[
        ('', 'Select...'),
        ('a', 'Option A'),
        ('b', 'Option B'),
        ('c', 'Option C'),
        ('d', 'Option D')
    ])
    explanation = TextAreaField('Explanation', validators=[Length(max=1000)])
    marks = IntegerField('Marks', validators=[NumberRange(min=1, max=100)], default=1)
    difficulty = SelectField('Difficulty', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')


class UserForm(FlaskForm):
    """Form for users."""
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    is_admin = BooleanField('Is Admin')
    submit = SubmitField('Save')


class ApprovalForm(FlaskForm):
    """Form for approving/rejecting content."""
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    reason = TextAreaField('Reason (for rejection)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit')
