from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_bcrypt import Bcrypt
from twilio.rest import Client
from datetime import datetime
from phonenumbers import NumberParseException, PhoneNumberFormat
import phonenumbers
from flask_paginate import Pagination, get_page_parameter
from flask import jsonify
from twilio.twiml.voice_response import VoiceResponse
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.voice_response import VoiceResponse, Gather



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

# Twilio configuration
account_sid = "AC6e1ab97118183178db556a1765ffc962"
auth_token = "07b957931327c85c42e9420b0efd5a06" 
client = Client(account_sid, auth_token)


class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login as Admin')

class OperatorLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login as Operator')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operator')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
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

class Script(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('User Type', choices=[('admin', 'Admin'), ('operator', 'Operator')], validators=[DataRequired()])
    submit = SubmitField('Login')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    area_id = SelectField('Area', coerce=int)
    submit = SubmitField('Add Contact')

class AreaForm(FlaskForm):
    name = StringField('Area Name', validators=[DataRequired()])
    submit = SubmitField('Add Area')

class FeedbackForm(FlaskForm):
    resident_id = SelectField('Resident', coerce=int)
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class ScriptForm(FlaskForm):
    name = StringField('Script Name', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save Script')

class CallForm(FlaskForm):
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Initiate Call')
class FeedbackForm(FlaskForm):
    resident_id = SelectField('Resident', coerce=int)
    message = TextAreaField('Feedback', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    form.resident_id.choices = [(contact.id, contact.name) for contact in Contact.query.all()]
    if form.validate_on_submit():
        feedback = Feedback(resident_id=form.resident_id.data, message=form.message.data)
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html', form=form)
@app.route('/admin/feedback')
@login_required
def admin_feedback():
    feedbacks = Feedback.query.all()
    return render_template('admin_feedback.html', feedbacks=feedbacks)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='admin').first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('admin_login.html', form=form)

@app.route('/operator_login', methods=['GET', 'POST'])
def operator_login():
    form = OperatorLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='operator').first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('operator_dashboard'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('operator_login.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role=form.user_type.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('operator_dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/initiate_call', methods=['GET', 'POST'])
def initiate_call():
    form = CallForm()
    form.area_id.choices = [(area.id, area.name) for area in Area.query.all()]

    # Check if it's a POST from ESP8266 JSON
    if request.method == 'POST':
        if request.is_json:
            print("Is JSON:", request.is_json)
            print("Raw data:", request.data)

            data = request.get_json()
            area_id = data.get('area_id')
            message = "The water has been opened."
        else:
            # Normal web form submission
            if form.validate_on_submit():
                area_id = form.area_id.data
                message = "The water has been opened."
            else:
                return render_template('initiate_call.html', form=form)

        residents = Contact.query.filter_by(area_id=area_id).all()
        for resident in residents:
            formatted_number = format_phone_number(resident.phone_number)
            if formatted_number:
                try:
                    call = client.calls.create(
                        to=formatted_number,
                        from_="+15705838159",  # Replace with your Twilio number
                        twiml=f'<Response><Say>{message}</Say></Response>'
                    )
                    print(f"Call SID: {call.sid}")
                    call_log = CallLog(status='initiated', area_id=area_id)
                    db.session.add(call_log)
                    db.session.commit()
                except Exception as e:
                    print(f"Failed to make call: {e}")
                    if not request.is_json:
                        flash(f'Failed to make call to {formatted_number}.', 'danger')
            else:
                if not request.is_json:
                    flash(f'Invalid phone number: {resident.phone_number}.', 'danger')

        if request.is_json:
            return jsonify({"status": "success"}), 200
        else:
            flash('Calls initiated successfully!', 'success')
            return redirect(url_for('call_logs'))

    return render_template('initiate_call.html', form=form)

@app.route('/manage_contacts', methods=['GET', 'POST'])
@login_required
def manage_contacts():
    contacts = Contact.query.all()
    areas = Area.query.all()  # Fetch all areas for dropdown
    form = ContactForm()

    # ✅ Ensure the area dropdown is populated correctly
    form.area_id.choices = [(area.id, area.name) for area in areas]

    if form.validate_on_submit():
        new_contact = Contact(
            name=form.name.data,
            phone_number=form.phone_number.data,
            area_id=form.area_id.data
        )
        db.session.add(new_contact)
        db.session.commit()
        flash('Contact added successfully', 'success')
        return redirect(url_for('manage_contacts'))

    return render_template('manage_contacts.html', contacts=contacts, form=form)

@app.route('/manage_areas', methods=['GET', 'POST'])
def manage_areas():
    form = AreaForm()
    if form.validate_on_submit():
        # Check if the area name already exists
        existing_area = Area.query.filter_by(name=form.name.data).first()
        if existing_area:
            flash('Area name already exists. Please choose a different name.', 'warning')
            return redirect(url_for('manage_areas'))

        # Add new area if it doesn't exist
        new_area = Area(name=form.name.data)
        db.session.add(new_area)
        db.session.commit()
        flash('Area added successfully!', 'success')
        return redirect(url_for('manage_areas'))

    areas = Area.query.all()
    return render_template('manage_areas.html', areas=areas, form=form)
@app.route('/delete_area/<int:area_id>', methods=['POST'])
def delete_area(area_id):
    area = Area.query.get_or_404(area_id)
    try:
        db.session.delete(area)
        db.session.commit()
        flash('Area deleted successfully!', 'success')
    except:
        db.session.rollback()
        flash('An error occurred while deleting the area.', 'danger')
    return redirect(url_for('manage_areas'))

@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    contact = Contact.query.get(contact_id)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully', 'success')
    else:
        flash('Contact not found', 'danger')
    return redirect(url_for('manage_contacts'))



@app.route('/report')
@login_required
def report():
    call_logs = CallLog.query.all()
    return render_template('report.html', call_logs=call_logs)

@app.route('/call_logs')
@login_required
def call_logs():
    call_logs = CallLog.query.all()
    areas = {area.id: area.name for area in Area.query.all()}
    return render_template('call_logs.html', call_logs=call_logs, areas=areas)
@app.route('/clear_call_logs', methods=['POST'])
def clear_call_logs():
    # Clear all call logs
    CallLog.query.delete()
    db.session.commit()  # Commit the changes
    flash('All call logs have been cleared!', 'success')  # Flash message for feedback
    return redirect(url_for('call_logs'))  # Redirect back to the call logs page

@app.route('/scripts', methods=['GET', 'POST'])
@login_required
def scripts():
    form = ScriptForm()
    if form.validate_on_submit():
        script = Script(name=form.name.data, content=form.content.data)
        db.session.add(script)
        db.session.commit()
        flash('Script saved successfully!', 'success')
        return redirect(url_for('scripts'))
    scripts = Script.query.all()
    return render_template('scripts.html', form=form, scripts=scripts)
@app.route('/test_call', methods=['GET'])
def test_call():
    try:
        call = client.calls.create(
            to='+15705838159',  # Replace with a valid phone number
            from_="YOUR_TWILIO_PHONE_NUMBER",  # Replace with your Twilio number
            twiml='<Response><Say>Hello from Twilio!</Say></Response>'
        )
        return f"Call initiated with SID: {call.sid}"
    except Exception as e:
        return f"Error: {e}"

@app.route('/manage_scripts', methods=['GET', 'POST'])
@login_required
def manage_scripts():
    form = ScriptForm()
    if form.validate_on_submit():
        script = Script(name=form.name.data, content=form.content.data)
        db.session.add(script)
        db.session.commit()
        flash('Script added successfully!', 'success')
    scripts = Script.query.all()
    return render_template('manage_scripts.html', form=form, scripts=scripts)


def format_phone_number(number):
    try:
        # Parse the number assuming it is from India
        parsed_number = phonenumbers.parse(number, "IN")

        # Check if the number is valid
        if not phonenumbers.is_valid_number(parsed_number):
            return None

        # Format the number in E.164 format
        formatted_number = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)

        return formatted_number
    except NumberParseException:
        return None

def create_default_users():
    with app.app_context():
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(email='admin@example.com', role='admin')
            admin.set_password('admin_password')
            db.session.add(admin)

        operator = User.query.filter_by(email='operator@example.com').first()
        if not operator:
            operator = User(email='operator@example.com', role='operator')
            operator.set_password('operatorpassword')
            db.session.add(operator)

        db.session.commit()


@app.route('/edit_contact/<int:contact_id>', methods=['POST'])
def edit_contact(contact_id):
    contact = Contact.query.get(contact_id)
    if contact is None:
        flash('Contact not found', 'danger')
        return redirect(url_for('manage_contacts'))

    contact.name = request.form['name']
    contact.phone_number = request.form['phone_number']
    contact.area_id = request.form['area_id']

    db.session.commit()
    flash('Contact updated successfully', 'success')
    return redirect(url_for('manage_contacts'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
@app.route('/operator_dashboard', endpoint='operator_dashboard')
def operator_dashboard():
    return render_template('operator_dashboard.html')
@app.route('/admin_dashboard', endpoint='admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route("/ivr", methods=["POST"])
def ivr():
    response = VoiceResponse()

    gather = Gather(num_digits=1, action='/handle-key', method='POST')
    gather.say("Vanakkam! Press 1 to report a water leakage. Press 2 for no water supply. Press 3 to talk to an operator.", language='ta-IN')
    response.append(gather)

    # If no input received
    response.redirect('/ivr')
    return Response(str(response), mimetype='text/xml')

@app.route("/handle-key", methods=["POST"])
def handle_key():
    digit_pressed = request.form.get('Digits')
    response = VoiceResponse()

    if digit_pressed == '1':
        response.say("Neenga water leakage report pannitinga. Ungal complaint register pannapatathu.", language='ta-IN')
    elif digit_pressed == '2':
        response.say("Neenga water supply illa-nu report pannitinga. Complaint register pannapatathu.", language='ta-IN')
    elif digit_pressed == '3':
        response.say("Oru operator-oda pesunga. Ippodhu call connect aagum.", language='ta-IN')
        response.dial("")  # Replace with your operator's number
    else:
        response.say("Thavaru input. Please try again.", language='ta-IN')
        response.redirect('/ivr')

    return Response(str(response), mimetype='text/xml')

@app.route("/complaints")
@login_required
def complaints():
    """Displays recorded complaints"""
    complaints = Complaint.query.all()
    return render_template("complaints.html", complaints=complaints)


@app.route('/trigger_alert', methods=['POST'])
def trigger_alert():
    data = request.get_json()  # Get JSON data from the request
    flow_count = data.get('flowCount')  # Extract the flow count value
    print(f"Received flow count: {flow_count}")

    # Do something with the flow count, e.g., trigger an alert or log the data

    return 'Data received successfully', 200
@app.route('/api/flow')
def receive_flow():
    value = request.args.get('value')
    # Save to database or log it
    print(f"Flow Value: {value}")
    return "Received", 200

    return 'Invalid action', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

