from flask import Blueprint, render_template
from flask_login import login_required
from .decorators import admin_only
from .models import Program, Event, Assignment, AssignmentCompletion, User, Attendance,ProgramAdmin, program_model
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from .extension import db
from flask import current_app
from .models import Event, Assignment
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_required, current_user, logout_user,  login_user
from datetime import datetime,date, time

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="../templates"  # relative to this file's location
)
def get_next_events(program_id, limit=5):
    with current_app.app_context():
        start_of_today = datetime.combine(date.today(), time.min)
        return (
            Event.query
            .filter(Event.program_id == program_id, Event.date >= start_of_today)
            .order_by(Event.date.asc())
            .limit(limit)
            .all()
        )
@main_bp.route("/")
def home():
    return render_template("home.html")

@main_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if check_password_hash(user.password_hash, password):
                login_user(user)
                if not db.session.get(ProgramAdmin,(user.program_id,user.school_id)):
                    return redirect(url_for("main.student_dashboard"))
                return redirect(url_for("main.admin_dashboard"))

            else:
                flash("incorrect password")
    return render_template("login.html")

@main_bp.route("/register", methods=["GET","POST"])
def register_student():
    if request.method == "POST":
        school_id = request.form.get("school_id")
        name = request.form.get("fname") + " " + request.form.get("lname")
        email = request.form.get("email")
        program_id = program_model.get(request.form.get("program").upper().strip())
        password = request.form.get("password")
        confirmpassword = request.form.get("confirm-password")
        if password == confirmpassword:
            hashed_password = generate_password_hash(password,method="scrypt",salt_length=8)
            program = db.session.get(Program, program_id)
            new_user = User(school_id = school_id,name=name,email=email,role="Student",password_hash=hashed_password,program=program)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("main.student_dashboard"))
        else:
            flash("Passwords Do Not Match")
    return render_template("register.html")

@main_bp.route("/register-admin", methods=["GET","POST"])
def register_admin():
    if request.method == "POST":
        school_id = request.form.get("school_id")
        name = request.form.get("fname") + " " + request.form.get("lname")
        email = request.form.get("email")
        program_id =  program_model.get(request.form.get("program").upper().strip())
        role = request.form.get("role")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirm-password")
        if password == confirmpassword:
            hashed_password = generate_password_hash(password,method="scrypt",salt_length=8)
            program = db.session.get(Program, program_id)
            new_user = User(school_id = school_id,name=name,email=email,role=role,password_hash=hashed_password,program=program)
            new_program_admin = ProgramAdmin(program=program,user=new_user)
            db.session.add_all([new_user,new_program_admin])
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("main.admin_dashboard"))
        else:
            flash("Passwords Do Not Match")
    return render_template("register-admin.html")

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("home.html")

@main_bp.route("/student")
@login_required
def student_dashboard():
    tasks = current_user.program.assignments
    events = get_next_events(current_user.program_id)
    return render_template("student-dashboard.html",tasks=tasks, events=events)

@main_bp.route("/admin")
@login_required
@admin_only
def admin_dashboard():
    tasks = current_user.program.assignments
    events = current_user.program.events
    return render_template("admin-dashboard.html",tasks=tasks,events=events)

@main_bp.route("/add-program",methods=["GET","POST"])
def create_program():
    if request.method == "POST":
        program_name = request.form.get("program")
        new_program = Program(name=program_name)
        db.session.add(new_program)
        db.session.commit()
        return redirect(url_for('main.home'))
    return render_template("add-program.html")

@main_bp.route("/create_task",methods=["GET","POST"])
@login_required
@admin_only
def create_task():
    #creates a new task for a program to be displayed on student and admin dashboards
    #a key thing to ensure is that the program field for admins is never nullable while testing make sure because if thi fails then there will be a lot of problems
    if request.method == "POST":
        program = db.session.get(Program, current_user.program_id)
        title  = request.form.get("title")
        description = request.form.get("description")
        deadline_str = request.form.get("deadline")
        deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
        new_task = Assignment(title=title,description=description,program=program,deadline=deadline)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("main.admin_dashboard"))
    return render_template("add-task.html")


@main_bp.route("/edit_task/<int:task_id>",methods=["GET","POST"])
@login_required
@admin_only
def edit_task(task_id):
    task = db.session.get(Assignment, task_id)
    if not task:
        flash("Task not found")
        return redirect(url_for("main.admin_dashboard"))
        
    if request.method == "POST":
        #make sure the names of fields in the form match the attribute names of the Assignment class
        form_data = {key:value for key,value in request.form.to_dict().items() if value}
        stmt = (
            db.update(Assignment)
            .where(Assignment.id == task_id)
            .values(form_data)
        )
        db.session.execute(stmt)
        db.session.commit()
        flash("Changes Have Been Made")
        return redirect(url_for("main.admin_dashboard"))
    return render_template("edit-task.html", task=task)


@main_bp.route("/delete_task/<int:task_id>")
@login_required
@admin_only
def delete_task(task_id):
    # edits existing task for a specific program
    stmt = db.delete(Assignment).where(Assignment.id == task_id)
    db.session.execute(stmt)
    db.session.commit()

    return redirect(url_for("main.admin_dashboard"))

@main_bp.route("/create_event",methods=["GET","POST"])
@login_required
@admin_only
def create_event():
    # creates a new event for a program to be displayed on student and admin dashboards
    if request.method == "POST":
        program = db.session.get(Program, current_user.program_id)
        title = request.form.get("title")
        code = request.form.get("code")
        description = request.form.get("description")
        location = request.form.get("location")
        date_str = request.form.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        new_event = Event(title=title, code=code,description=description, program=program, location=location,date=date)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for("main.admin_dashboard"))
    return render_template("add-event.html")



@main_bp.route("/edit_event/<int:event_id>",methods=["GET","POST"])
@login_required
@admin_only
def edit_event(event_id):
    # edits existing events for a specific program
    event = db.session.get(Event, event_id)
    if not event:
        flash("Event not found")
        return redirect(url_for("main.admin_dashboard"))
        
    if request.method == "POST":
        # make sure the names of fields in the form match the attribute names of the Event class
        form_data = {key: value for key, value in request.form.to_dict().items() if value}
        form_data["date"] = datetime.strptime(form_data["date"], "%Y-%m-%dT%H:%M")
        stmt = (
            db.update(Event)
            .where(Event.id == event_id)
            .values(form_data)
        )
        db.session.execute(stmt)
        db.session.commit()
        flash("Changes Have Been Made")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("edit-event.html", event=event)


@main_bp.route("/delete_event/<int:event_id>")
@login_required
@admin_only
def delete_event(event_id):
    # deletes existing events for a specific program
    stmt = db.delete(Event).where(Event.id == event_id)
    db.session.execute(stmt)
    db.session.commit()

    return redirect(url_for("main.admin_dashboard"))

@main_bp.route("/edit-student")
@login_required
@admin_only
def edit_student():
    return


#TODO - create a way for students to sign in to events
#TODO - create a way for admins to view students who attended a particular event
#TODO - create a way for admins to signify a student submitted an assignment

""" So when the students sign in and view their dashboard they should vie the list of events if they click on one 
it should take them to a new page where the see a description of the event with an option to sign in with a code
 when they submit with the right code it should take them back to their dashboard but create a record in the attendance table
"""
@main_bp.route("/sign-in/<int:event_id>",methods=["GET","POST"])
@login_required
def sign_in(event_id):
    event = db.session.get(Event, event_id)
    if request.method == "POST":
        if request.form.get("code") == event.code:
            db.session.add(Attendance(user=current_user,event=event))
            db.session.commit()
            return redirect(url_for("main.student_dashboard"))
        flash("Incorrect Code")
    return render_template("sign-in-to-event.html",event=event)

@main_bp.route("/view-attendance/<int:event_id>")
@login_required
@admin_only
def view_attendance(event_id):
    event = db.session.get(Event,event_id)
    return render_template("attendance.html",attendance=event.attendance,event_id=event_id)

@main_bp.route("/edit-attendance/<int:event_id>",methods=["GET","POST"])
@login_required
@admin_only
def edit_attendance(event_id):
    if request.method == "POST":
        full_name = (request.form.get("fname") + " " + request.form.get("lname")).lower().strip()
        event = db.session.get(Event, event_id)
        user = (
            db.session.execute(
            db.select(User)
            .join(User.program)
            .join(Program.events)
            .where(Event.id == event_id, db.func.lower(User.name) == full_name.lower())
            ).scalar()
        )
        db.session.add(Attendance(user=user,event=event))
        db.session.commit()
        return redirect(url_for("main.view_attendance",event_id=event_id))
    return render_template("edit-attendance.html",event_id=event_id)


@main_bp.route("/delete-attendance/<int:event_id>/<int:user_id>")
@login_required
@admin_only
def delete_attendance(event_id,user_id):
    attendance = db.session.get(Attendance,(event_id,user_id))
    if attendance:
        db.session.delete(attendance)
        db.session.commit()
    return redirect(url_for("main.view_attendance",event_id=event_id))


@main_bp.route("/assignment-completion/<int:task_id>",methods=["GET","POST"])
@login_required
@admin_only
def assignment_completion(task_id):
    if request.method == "POST":
        user_ids = request.form.getlist("present")
        for id in user_ids:
            db.session.add(AssignmentCompletion(user_id=id,assignment_id=task_id))
        db.session.commit()
        return redirect(url_for("main.admin_dashboard"))
    task = db.session.get(Assignment, task_id)
    return render_template("assignment-completion.html",attendance=task.program.users,task_id=task_id)

#TODO - for assignments i want to figure out a way for admins to select students who submitted  using a checkbox feature
#TODO - Implement changes to the models to  include timestamps to all models

