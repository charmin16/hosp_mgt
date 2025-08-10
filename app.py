from flask import Flask, request, redirect, render_template, url_for, flash, session
from database import Patients, Visits, Doctors, PatientLogin, app, db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

app.secret_key = '123'


@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing = Doctors.query.filter(
            or_(Doctors.username == username,
                Doctors.staff_id == username)
        ).first()

        if existing and check_password_hash(existing.password, password):
            session['doctor'] = existing.username
            session['name'] = existing.name
            session['staff_id'] = existing.staff_id

            flash('Login Successful', category='success')
            return redirect(url_for('home'))

        flash('Invalid username or password', category='error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('Name')
        staff_id = request.form.get('StaffID')
        username = request.form['username']
        password = request.form['password']

        existing = Doctors.query.filter(Doctors.staff_id == staff_id).first()

        if existing and check_password_hash(existing.password, password):
            flash(f'Staff ID {staff_id} Has already been registered. If its you then login below or re-check your id and register', category='error')
            return redirect(url_for('login'))

        hashed = generate_password_hash(password)

        new_doc = Doctors(
            name=name,
            staff_id=staff_id,
            username=username,
            password=hashed
        )

        db.session().add(new_doc)
        db.session().commit()

        flash('Registration Successful. Login Below', category='success')
        return redirect(url_for('login'))

    return render_template('register_doc.html')


@app.route('/home/')
def home():
    if 'doctor' not in session:
        flash('You must be logged in to access this page', category='error')
        return redirect(url_for('login'))

    doc = session['name']
    return render_template('home.html', doc=doc)


@app.route('/add/', methods=['POST', 'GET'])
def add_patient():
    if 'doctor' not in session:
        flash('You must be logged in to access this page', category='error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get all form data
        form_data = {
            'name': request.form['name'],
            'gender': request.form['gender'],
            'dob': request.form['dob'],
            'patient': request.form['patient'],
            'nok': request.form['nok'],
            'biw': request.form['biw'],
            'bid': request.form.get('bid'),
            'blood': request.form.get('blood')
        }

        # Validate phone number length
        if len(form_data['patient']) != 11:
            flash('Phone Number must be 11 digits long', category='error')
            return render_template('add_pat.html', form_data=form_data)

        try:
            age_date = datetime.strptime(form_data['dob'], '%Y-%m-%d').date()
            this_year = date.today().year
            age = this_year - age_date.year

            bid = datetime.strptime(form_data['bid'], '%Y-%m-%d').date() if form_data['bid'] else datetime.now().date()

            new_patient = Patients(
                name=form_data['name'],
                gender=form_data['gender'],
                age=age,
                next_of_kin=form_data['nok'],
                patient_phone=form_data['patient'],
                blood_group=form_data['blood'],
                presenting_complaint=form_data['biw'],
                admission_date=bid
            )

            db.session.add(new_patient)
            db.session.commit()
            return render_template('add_success.html', new_patient=new_patient)

        except IntegrityError:
            flash('This Phone Number is already in the database', category='error')
            return render_template('add_pat.html', form_data=form_data)

    # For GET requests or initial load
    return render_template('add_pat.html', form_data={})


@app.route('/search/', methods=['POST', 'GET'])
def search_phone():
    if request.method == 'POST':
        tel = request.form['phone']

        patient = Patients.query.filter(Patients.patient_phone == tel).first()

        if patient:
            visit = Visits.query.filter(Visits.patient_id == patient.id).all()
            return render_template('add_visit.html', visit=visit, patient=patient)

        flash('Phone Number not Found. Please check the number and try again', category='error')
        return redirect(url_for('home'))

    # return render_template('search_phone.html')


@app.route('/search_name/', methods=['POST', 'GET'])
def search_name():
    if request.method == 'POST':
        pat_name = request.form['name'].strip()
        names = Patients.query.filter(Patients.name.ilike(f'%{pat_name}%')).all()

        if names:
            if len(names) > 1:
                return render_template('search_name_res.html', names=names)
            elif len(names) == 1:
                return redirect(url_for('log_visit', phone=names[0].patient_phone))

        flash(f'Name Does Not Exist. Try Again or Register {pat_name}', category='error')
        return redirect(url_for('home'))


@app.route('/search_name/<int:id>')
def name_details(id):
    name = Patients.query.filter(Patients.id == id).first()
    # visit = Visits.query.filter(Visits.patient_id == name.id).first()
    return redirect(url_for('log_visit', phone=name.patient_phone))


@app.route('/add_visit/<string:phone>', methods=['POST', 'GET'])
def log_visit(phone):
    doc = session['name']
    now = datetime.now()
    now = datetime.strftime(now, '%Y-%m-%d %H:%M')
    log_patient = Patients.query.filter(Patients.patient_phone == phone).first()
    add_visit = Visits.query.filter(Visits.patient_id == log_patient.id).order_by(Visits.date).all()
    # latest_visit = Visits.query.filter_by(patient_id=log_patient.id).order_by(Visits.id.desc()).first()

    if request.method == 'POST':
        visit_date = request.form['date']
        diag = request.form['diagnosis']
        test = request.form['test']
        medication = request.form['medication']
        next_date = request.form.get('next_date')
        # doctor = request.form['doctor']

        if not visit_date:
            visit_date = date.today()

        new_visit = Visits(
            date=visit_date,
            diagnosis=diag,
            tests=test,
            medication=medication,
            attending_physician=f'Dr {doc}',
            next_appointment=next_date,
            patient_id=log_patient.id
        )

        db.session.add(new_visit)
        db.session.commit()
        latest_visit = Visits.query.filter_by(patient_id=log_patient.id).order_by(Visits.id.desc()).first()

        return render_template('add_visit_outcome.html', patient=log_patient, visit=latest_visit, now=now)

    return render_template('add_visit.html', visit=add_visit, patient=log_patient)


@app.route('/search_patient', methods=['POST', 'GET'])
def search_patient():
    search_type = request.form.get('search_type', 'phone')
    query = request.form.get('query', '').strip()

    if not query:
        flash('Please Enter Search Criteria', 'error')
        return redirect(request.referrer)
    if search_type == 'phone':
        patient = Patients.query.filter(Patients.patient_phone == query).first()
    else:
        patient = Patients.query.filter(Patients.name.ilike(f'%{query}%')).first()

    if patient:
        visits = Visits.query.filter_by(patient_id=patient.id).order_by(Visits.date.desc()).all()
        now = datetime.now().strftime ('%Y-%m-%d %H:%M')

        return render_template('add_visit.html',
                               patient=patient,
                               visit=visits,  # Note: using 'visit' to match your template
                               now=now)

    else:
        flash('Patient Not Found', 'error')
        return redirect(url_for('search_patient'))


@app.route('/vitals/<string:phone>')
def core_vitals(phone):
    pat_vitals = Patients.query.filter(Patients.patient_phone == phone).first()
    return render_template('core.html', pat_vitals=pat_vitals)


@app.route('/register_patient', methods=['POST', 'GET'])
def reg_patient():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        password = request.form.get('password')

        hashed = generate_password_hash(password)

        if Patients.query.filter(Patients.patient_phone == phone).first():
            new_reg = PatientLogin(
                name=name,
                phone=phone,
                password=hashed
            )
            db.session.add(new_reg)
            db.session.commit()
            flash('Patient Successfully Registered. You can now sign in as patient to view your own records')
            return redirect(url_for('login'))

        flash('Credentials not in our database. Are you sure you have visited our facility before', 'error')
        return redirect(url_for('reg_patient'))

    return render_template('register_pat.html')


@app.route('/login_patient', methods=['POST', 'GET'])
def log_patient():
    if request.method == 'POST':
        phone = request.form.get('pat_tel')
        password = request.form.get('pat_password')

        existing = PatientLogin.query.filter(PatientLogin.phone == phone).first()
        if existing and check_password_hash(existing.password, password):
            pat_single = Patients.query.filter(Patients.patient_phone == existing.phone).first()
            add_visit = Visits.query.filter(Visits.patient_id == pat_single.id).all()
            flash('Login Successful', 'success')
            return render_template('patient_page.html', patient=pat_single, visit=add_visit)
        else:
            flash('Credentials Not Found', 'error')
            return render_template('register_pat.html')

    return redirect(url_for('login'))


@app.route('/update/<string:phone>/<int:visit_id>', methods=['POST', 'GET'])
def update(phone, visit_id):
    single = Patients.query.filter(Patients.patient_phone == phone).first_or_404()
    vis = Visits.query.filter_by(id=visit_id, patient_id=single.id).first_or_404()

    if request.method == 'POST':
        diag = request.form['diagnosis']
        test = request.form['test']
        medication = request.form['medication']

        vis.diagnosis = diag
        vis.tests = test
        vis.medication = medication

        db.session.commit()
        flash('Medical Record Successfully Updated', category='success')
        return redirect(url_for('log_visit', phone=phone))

    return render_template('edit_visit.html', vis=vis, single=single)


@app.route('/delete/<string:phone>/<int:visit_id>')
def delete(phone, visit_id):
    single = Patients.query.filter_by(patient_phone=phone).first_or_404()
    vis = Visits.query.filter_by(id=visit_id, patient_id=single.id).first_or_404()

    db.session.delete(vis)
    db.session.commit()
    flash('Medical Record Deleted', category='success')
    return redirect(url_for('log_visit', phone=phone))


@app.route('/logout')
def logout():
    session.pop('doctor', None)  # Remove doctor from session
    flash('You have been logged out', category='success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5003)





