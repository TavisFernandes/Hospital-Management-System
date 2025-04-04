from flask import Flask,render_template,request,session,redirect,url_for,flash
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
# from flask_mail import Mail
import json



# MY db connection
local_server= True
app = Flask(__name__)
app.secret_key='hmsprojects'


# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

# SMTP MAIL SERVER SETTINGS

# app.config.update(
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT='465',
#     MAIL_USE_SSL=True,
#     MAIL_USERNAME="add your gmail-id",
#     MAIL_PASSWORD="add your gmail-password"
# )
# mail = Mail(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/hms'
db=SQLAlchemy(app)



# here we will create db models that is tables
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    usertype=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))

class Patients(db.Model):
    pid=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    name=db.Column(db.String(50))
    gender=db.Column(db.String(50))
    slot=db.Column(db.String(50))
    disease=db.Column(db.String(50))
    time=db.Column(db.String(50),nullable=False)
    date=db.Column(db.String(50),nullable=False)
    dept=db.Column(db.String(50))
    number=db.Column(db.String(50))
    status=db.Column(db.String(20), default='active', nullable=True)  # 'active' or 'cancelled'

class Doctors(db.Model):
    did=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    doctorname=db.Column(db.String(50))
    dept=db.Column(db.String(50))

class Trigr(db.Model):
    tid=db.Column(db.Integer,primary_key=True)
    pid=db.Column(db.Integer)
    email=db.Column(db.String(50))
    name=db.Column(db.String(50))
    action=db.Column(db.String(50))
    timestamp=db.Column(db.String(50))

class Prescriptions(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    patient_id=db.Column(db.Integer)
    doctor_id=db.Column(db.Integer)
    medication=db.Column(db.Text)
    dosage=db.Column(db.String(100))
    instructions=db.Column(db.Text)
    date_prescribed=db.Column(db.DateTime, server_default=db.func.now())
    status=db.Column(db.String(20))

class DoctorAvailability(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    doctor_id=db.Column(db.Integer)
    day_of_week=db.Column(db.String(10))
    start_time=db.Column(db.Time)
    end_time=db.Column(db.Time)
    is_available=db.Column(db.Boolean)

class AppointmentReminders(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    appointment_id=db.Column(db.Integer)
    reminder_time=db.Column(db.DateTime)
    reminder_sent=db.Column(db.Boolean)
    reminder_method=db.Column(db.String(10))

class CancellationNotifications(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    patient_id=db.Column(db.Integer)
    doctor_id=db.Column(db.Integer)
    appointment_id=db.Column(db.Integer)
    message=db.Column(db.String(200))
    created_at=db.Column(db.DateTime, server_default=db.func.now())
    is_read=db.Column(db.Boolean, default=False)





# here we will pass endpoints and run the fuction
@app.route('/')
def index():
    return render_template('index.html')
    


@app.route('/doctors',methods=['POST','GET'])
def doctors():

    if request.method=="POST":

        email=request.form.get('email')
        doctorname=request.form.get('doctorname')
        dept=request.form.get('dept')

        # query=db.engine.execute(f"INSERT INTO `doctors` (`email`,`doctorname`,`dept`) VALUES ('{email}','{doctorname}','{dept}')")
        query=Doctors(email=email,doctorname=doctorname,dept=dept)
        db.session.add(query)
        db.session.commit()
        flash("Information is Stored","primary")

    return render_template('doctor.html')



@app.route('/patients',methods=['POST','GET'])
@login_required
def patient():
    doct=Doctors.query.all()

    if request.method=="POST":
        email=request.form.get('email')
        name=request.form.get('name')
        gender=request.form.get('gender')
        slot=request.form.get('slot')
        disease=request.form.get('disease')
        time=request.form.get('time')
        date=request.form.get('date')
        dept=request.form.get('dept')
        number=request.form.get('number')
        
        if len(number)<10 or len(number)>10:
            flash("Please give 10 digit number")
            return render_template('patient.html',doct=doct)

        # Create appointment
        appointment = Patients(
            email=email,
            name=name,
            gender=gender,
            slot=slot,
            disease=disease,
            time=time,
            date=date,
            dept=dept,
            number=number
        )
        db.session.add(appointment)
        db.session.commit()
        
        # Schedule reminders
        from datetime import datetime, timedelta
        appointment_date = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        # 24-hour reminder
        reminder_24h = AppointmentReminders(
            appointment_id=appointment.pid,
            reminder_time=appointment_date - timedelta(hours=24),
            reminder_method='email'
        )
        
        # 1-hour reminder
        reminder_1h = AppointmentReminders(
            appointment_id=appointment.pid,
            reminder_time=appointment_date - timedelta(hours=1),
            reminder_method='sms'
        )
        
        db.session.add(reminder_24h)
        db.session.add(reminder_1h)
        db.session.commit()
        
        # mail starts from here

        # mail.send_message(subject, sender=params['gmail-user'], recipients=[email],body=f"YOUR bOOKING IS CONFIRMED THANKS FOR CHOOSING US \nYour Entered Details are :\nName: {name}\nSlot: {slot}")



        flash("Booking Confirmed","info")


    return render_template('patient.html',doct=doct)


@app.route('/bookings')
@login_required
def bookings(): 
    em = current_user.email
    if current_user.usertype == "Doctor":
        # For doctors: show all bookings and their availability
        query = Patients.query.all()
        availability = DoctorAvailability.query.filter_by(doctor_id=current_user.id).all()
        return render_template('booking.html',
                            query=query,
                            availability=availability,
                            is_doctor=True)
    else:
        # For patients: show their bookings and doctor availability
        query = Patients.query.filter_by(email=em)
        # Filter out cancelled appointments if status column exists
        if hasattr(Patients, 'status'):
            query = query.filter(Patients.status != 'cancelled')
        doctors = Doctors.query.all()
        availability = []
        for doctor in doctors:
            avail = DoctorAvailability.query.filter_by(doctor_id=doctor.did, is_available=True).all()
            availability.extend(avail)
        return render_template('booking.html',
                            query=query,
                            availability=availability,
                            is_doctor=False,
                            doctors=Doctors.query.all())
    


@app.route("/edit/<string:pid>",methods=['POST','GET'])
@login_required
def edit(pid):    
    if request.method=="POST":
        email=request.form.get('email')
        name=request.form.get('name')
        gender=request.form.get('gender')
        slot=request.form.get('slot')
        disease=request.form.get('disease')
        time=request.form.get('time')
        date=request.form.get('date')
        dept=request.form.get('dept')
        number=request.form.get('number')
        # db.engine.execute(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', `slot` = '{slot}', `disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}', `number` = '{number}' WHERE `patients`.`pid` = {pid}")
        post=Patients.query.filter_by(pid=pid).first()
        post.email=email
        post.name=name
        post.gender=gender
        post.slot=slot
        post.disease=disease
        post.time=time
        post.date=date
        post.dept=dept
        post.number=number
        db.session.commit()

        flash("Slot is Updates","success")
        return redirect('/bookings')
        
    posts=Patients.query.filter_by(pid=pid).first()
    return render_template('edit.html',posts=posts)


@app.route("/delete/<string:pid>",methods=['POST','GET'])
@login_required
def delete(pid):
    if current_user.usertype != "Doctor":
        flash("Only doctors can delete bookings", "danger")
        return redirect('/bookings')
    query=Patients.query.filter_by(pid=pid).first()
    db.session.delete(query)
    db.session.commit()
    flash("Booking Deleted Successfully","danger")
    return redirect('/bookings')

@app.route("/cancel/<string:pid>",methods=['POST','GET'])
@login_required
def cancel(pid):
    if current_user.usertype == "Doctor":
        flash("Doctors should use delete instead", "warning")
        return redirect('/bookings')
    query=Patients.query.filter_by(pid=pid).first()
    if query.email != current_user.email:
        flash("You can only cancel your own bookings", "danger")
        return redirect('/bookings')
    # Mark as cancelled if status column exists
    if hasattr(Patients, 'status'):
        query.status = 'cancelled'
    
    # Find the doctor for this appointment
    doctor = Doctors.query.filter_by(dept=query.dept).first()
    if doctor:
        # Create cancellation notification
        notification = CancellationNotifications(
            patient_id=query.pid,
            doctor_id=doctor.did,
            appointment_id=query.pid,
            message=f"Patient {query.name} cancelled booking for {query.date} {query.time}"
        )
        db.session.add(notification)
    
    db.session.commit()
    flash("Booking Cancelled - Note: Your payment may not be fully refunded", "warning")
    return redirect('/bookings')






@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == "POST":
        username=request.form.get('username')
        usertype=request.form.get('usertype')
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        # encpassword=generate_password_hash(password)
        if user:
            flash("Email Already Exist","warning")
            return render_template('/signup.html')

        # new_user=db.engine.execute(f"INSERT INTO `user` (`username`,`usertype`,`email`,`password`) VALUES ('{username}','{usertype}','{email}','{encpassword}')")
        myquery=User(username=username,usertype=usertype,email=email,password=password)
        db.session.add(myquery)
        db.session.commit()
        flash("Signup Succes Please Login","success")
        return render_template('login.html')

          

    return render_template('signup.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            flash("Login Success","primary")
            if user.usertype == "Doctor":
                # Check for unread cancellation notifications
                notifications = CancellationNotifications.query.filter(
                    CancellationNotifications.doctor_id == user.id,
                    CancellationNotifications.is_read == False
                ).order_by(CancellationNotifications.created_at.desc()).all()
                
                if notifications:
                    session['show_cancellation_popup'] = True
                    session['cancellations'] = [n.message for n in notifications]
                    # Mark notifications as read
                    for note in notifications:
                        note.is_read = True
                    db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","danger")
            return render_template('login.html')    





    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))



# Prescription System Routes
@app.route('/prescribe', methods=['POST','GET'])
@login_required
def prescribe():
    if current_user.usertype != "Doctor":
        flash("Only doctors can prescribe medications", "danger")
        return redirect(url_for('index'))
    
    patients = Patients.query.all()  # Get patients list first
    
    if request.method == "POST":
        patient_email = request.form.get('patient_email')
        medication = request.form.get('medication')
        dosage = request.form.get('dosage')
        instructions = request.form.get('instructions')
        
        patient = Patients.query.filter_by(email=patient_email).first()
        if not patient:
            flash("Patient not found", "danger")
            return render_template('prescribe.html', patients=patients)
            
        prescription = Prescriptions(
            patient_id=patient.pid,
            doctor_id=current_user.id,
            medication=medication,
            dosage=dosage,
            instructions=instructions
        )
        db.session.add(prescription)
        db.session.commit()
        flash("Prescription created successfully", "success")
        return redirect(url_for('view_prescriptions'))
    
    return render_template('prescribe.html', patients=patients)

@app.route('/availability', methods=['POST','GET'])
@login_required
def manage_availability():
    if current_user.usertype != "Doctor":
        flash("Only doctors can manage availability", "danger")
        return redirect(url_for('index'))
    
    if request.method == "POST":
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        available = bool(request.form.get('available'))
        
        # Convert time strings to time objects
        from datetime import time
        start = time.fromisoformat(start_time)
        end = time.fromisoformat(end_time)
        
        availability = DoctorAvailability(
            doctor_id=current_user.id,
            day_of_week=day,
            start_time=start,
            end_time=end,
            is_available=available
        )
        db.session.add(availability)
        db.session.commit()
        flash("Availability updated successfully", "success")
        return redirect(url_for('manage_availability'))
    
    # Get doctor's current availability
    availability = DoctorAvailability.query.filter_by(doctor_id=current_user.id).all()
    return render_template('availability.html', availability=availability)

@app.route('/check_availability/<int:doctor_id>')
@login_required
def check_availability(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, usertype="Doctor").first()
    if not doctor:
        flash("Doctor not found", "danger")
        return redirect(url_for('index'))
    
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id, is_available=True).all()
    return render_template('check_availability.html', doctor=doctor, availability=availability)

@app.route('/prescriptions')
@login_required
def view_prescriptions():
    # Get all prescriptions for current user
    if current_user.usertype == "Doctor":
        prescriptions = Prescriptions.query.filter_by(doctor_id=current_user.id).all()
    else:
        patient = Patients.query.filter_by(email=current_user.email).first()
        prescriptions = Prescriptions.query.filter_by(patient_id=patient.pid).all()

    # Pre-load all related data
    patient_data = {p.pid: p for p in Patients.query.all()}
    doctor_data = {d.id: d for d in User.query.filter_by(usertype='Doctor').all()}

    # Prepare prescription data with all required information
    prescription_list = []
    for p in prescriptions:
        prescription_list.append({
            'prescription': p,
            'patient': patient_data.get(p.patient_id),
            'doctor': doctor_data.get(p.doctor_id)
        })

    return render_template('prescriptions.html', 
                        prescriptions=prescription_list,
                        current_user=current_user)

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'
    

@app.route('/details')
@login_required
def details():
    posts=Trigr.query.all()
    # posts=db.engine.execute("SELECT * FROM `trigr`")
    return render_template('trigers.html',posts=posts)


@app.route('/search',methods=['POST','GET'])
@login_required
def search():
    if request.method=="POST":
        query=request.form.get('search')
        dept=Doctors.query.filter_by(dept=query).first()
        name=Doctors.query.filter_by(doctorname=query).first()
        if name:

            flash("Doctor is Available","info")
        else:

            flash("Doctor is Not Available","danger")
    return render_template('index.html')






from threading import Thread
from time import sleep
from datetime import datetime

def send_reminders():
    while True:
        try:
            with app.app_context():
                # First ensure all tables exist
                db.create_all()
                
                now = datetime.now()
                reminders = AppointmentReminders.query.filter(
                    AppointmentReminders.reminder_time <= now,
                    AppointmentReminders.reminder_sent == False
                ).all()
            
            for reminder in reminders:
                appointment = Patients.query.get(reminder.appointment_id)
                if appointment:
                    # In a real implementation, you would send email/SMS here
                    print(f"Sending {reminder.reminder_method} reminder for appointment ID {reminder.appointment_id}")
                    
                    # Mark reminder as sent
                    reminder.reminder_sent = True
                    db.session.commit()
                    
        except Exception as e:
            print(f"Error sending reminders: {str(e)}")
            
        sleep(60)  # Check every minute

# Initialize database and start reminder thread
with app.app_context():
    db.create_all()
    print("Database tables verified/created")

# Start reminder thread when not in debug mode
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    reminder_thread = Thread(target=send_reminders)
    reminder_thread.daemon = True
    reminder_thread.start()

def check_and_add_status_column():
    try:
        # Check if status column exists
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('patients')
        status_exists = any(col['name'] == 'status' for col in columns)
        
        if not status_exists:
            with db.engine.connect() as connection:
                connection.execute(db.text("ALTER TABLE patients ADD COLUMN status VARCHAR(20) DEFAULT 'active'"))
                connection.commit()
            print("Added status column to patients table")
    except Exception as e:
        print(f"Error checking/adding status column: {e}")

if __name__ == '__main__':
    with app.app_context():
        check_and_add_status_column()
    app.run(debug=True)

