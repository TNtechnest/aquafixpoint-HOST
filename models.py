from app import db

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contacts = db.relationship('Contact', backref='area', lazy=True)

class CallLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Contact')
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

