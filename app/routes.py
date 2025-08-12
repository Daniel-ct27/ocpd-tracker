from flask import Blueprint, render_template
from flask_login import login_required
from .decorators import admin_only
from .models import Program, Event, Assignment, AssignmentCompletion, User, Attendance,ProgramAdmin, program_model
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_required, current_user, logout_user,  login_user

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="../templates"  # relative to this file's location
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
                if not db.session.get(ProgramAdmin,(user.program_id,user.id)):
                    return redirect(url_for("main.student_dashboard"))
                return redirect(url_for("main.admin_dashboard"))

            else:
                flash("incorrect password")
    return render_template("login.html")

@main_bp.route("/register", methods=["GET","POST"])
def register_student():
    if request.method == "POST":
        name = request.form.get("fname") + " " + request.form.get("lname")
        email = request.form.get("email")
        password = request.form.get("password")
        program_id =  program_model.get(request.form.get("program").upper())
        confirmpassword = request.form.get("confirm-password")
        if password == confirmpassword:
            hashed_password = generate_password_hash(password,method="scrypt",salt_length=8)
            program = db.session.get(Program, program_id)
            new_user = User(name=name, email=email, password_hash=hashed_password, program=program)
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
        name = request.form.get("fname") + " " + request.form.get("lname")
        email = request.form.get("email")
        password = request.form.get("password")
        program_id =  program_model.get(request.form.get("program").upper().strip())
        confirmpassword = request.form.get("confirm-password")
        if password == confirmpassword:
            hashed_password = generate_password_hash(password,method="scrypt",salt_length=8)
            program = db.session.get(Program, program_id)
            new_user = User(name=name,email=email,password_hash=hashed_password,program=program)
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
    events = current_user.program.events
    return render_template("student-dashboard.html",tasks=tasks, events=events)

@main_bp.route("/admin")
@login_required
@admin_only
def admin_dashboard():
    tasks = current_user.program.assignments
    events = current_user.program.events
    return render_template("admin-dashboard.html",tasks=tasks,events=events)

@main_bp.route("/add-program",methods=["GET","POST"])
@login_required
@admin_only
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
        new_task = Assignment(title=title,description=description,program=program)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("main.admin_dashboard"))
    return render_template("add-task.html")


@main_bp.route("/edit_task/<int:task_id>",methods=["GET","POST"])
@login_required
@admin_only
def edit_task(task_id):
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
    return render_template("edit-task.html")


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
        new_event = Event(title=title, code=code,description=description, program=program)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for("main.admin_dashboard"))
    return render_template("add-event.html")



@main_bp.route("/edit_event/<int:event_id>",methods=["GET","POST"])
@login_required
@admin_only
def edit_event(event_id):
    # edits existing events for a specific program
    if request.method == "POST":
        # make sure the names of fields in the form match the attribute names of the Assignment class
        form_data = {key: value for key, value in request.form.to_dict().items() if value}
        stmt = (
            db.update(Event)
            .where(Event.id == event_id)
            .values(form_data)
        )
        db.session.execute(stmt)
        db.session.commit()
        flash("Changes Have Been Made")
        return redirect(url_for("main.admin_dashboard"))

    return render_template("edit-event.html")


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
