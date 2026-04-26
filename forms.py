from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EmployeeForm(FlaskForm):
    FullName = StringField('Full Name', validators=[DataRequired()])
    CNIC = StringField('CNIC', validators=[Optional()])
    Phone = StringField('Phone', validators=[Optional()])
    JobID = IntegerField('JobID', validators=[Optional()])
    ShiftID = IntegerField('ShiftID', validators=[Optional()])
    submit = SubmitField('Save')

class BusForm(FlaskForm):
    BusNumber = StringField('Bus Number', validators=[DataRequired()])
    Model = StringField('Model', validators=[Optional()])
    Capacity = IntegerField('Capacity', validators=[Optional()])
    RouteID = IntegerField('RouteID', validators=[Optional()])
    CategoryID = IntegerField('CategoryID', validators=[Optional()])
    submit = SubmitField('Save')

class TripForm(FlaskForm):
    RouteID = IntegerField('RouteID', validators=[DataRequired()])
    BusID = IntegerField('BusID', validators=[DataRequired()])
    DriverID = IntegerField('DriverID', validators=[Optional()])
    DepartureDateTime = StringField('Departure', validators=[DataRequired()])
    ArrivalDateTime = StringField('Arrival', validators=[DataRequired()])
    submit = SubmitField('Save')
