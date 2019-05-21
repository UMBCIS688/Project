from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, UserMixin, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="###########",
    password="###########",
    hostname="#########.mysql.pythonanywhere-services.com",
    databasename="################",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.secret_key = "################"
login_manager = LoginManager()
login_manager.init_app(app)


class Users(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_users(user_id):
    return Users.query.filter_by(username=user_id).first()

class Students(db.Model):
	__tablename__ = "students"

	studentid = db.Column(db.Integer, primary_key=True)
	fname = db.Column(db.String(35))
	lname = db.Column(db.String(35))
	major = db.Column(db.String(35))
	email = db.Column(db.String(256))
	grades = db.relationship("Grades", cascade="all, delete, delete-orphan") #for referencing grades directly from students class (ie.. students.grades)

class Course(db.Model):

	__tablename__ = "course"

	courseid = db.Column(db.Integer, primary_key=True)
	coursename = db.Column(db.String(50))
	courseinstructor = db.Column(db.String(70))

class Assignments(db.Model):

    __tablename__ = "assignments"

    assignmentid = db.Column(db.Integer, primary_key=True)
    assignmentname = db.Column(db.String(35))
    grades = db.relationship('Grades', cascade="all, delete, delete-orphan")


class Grades(db.Model):
	__tablename__ = "grades"

	#studentid = Links to primary key in table Student
	studentid = db.Column(db.Integer, db.ForeignKey('students.studentid', ondelete='cascade'), primary_key=True)
	assignmentid = db.Column(db.Integer, db.ForeignKey('assignments.assignmentid', ondelete='cascade'), primary_key=True)
	assignmentgrade = db.Column(db.Integer)
	students = db.relationship("Students", back_populates="grades")
	assignments = db.relationship("Assignments", back_populates="grades")

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("index.html", courseinfo=Course.query.first())

@app.route('/courseinfo', methods=["GET", "POST"])
def courseinfo():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":
        return render_template("course_main.html", courseinfo=Course.query.first())

    else:
        courseid=request.form["courseid"]
        coursename=request.form["coursename"]
        instructorname=request.form["instructorname"]
        updatecourse=Course(courseid=courseid,coursename=coursename,courseinstructor=instructorname)
        db.session.merge(updatecourse)
        db.session.commit()
        return redirect(url_for('courseinfo'))

@app.route('/roster', methods=["GET", "POST"])
def roster():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":
        return render_template("roster_main.html", courseroster=Students.query.all(), courseinfo=Course.query.first())

    elif request.form["rosterselection"]== "deletestudent":
        studentid_to_delete=request.form["studentid_to_delete"]
        Students.query.filter_by(studentid=studentid_to_delete).delete()
        db.session.commit()
        return render_template("roster_main.html", courseroster=Students.query.all(), courseinfo=Course.query.first())

    elif request.form["rosterselection"]== "addstudent":
        newstudent = Students(studentid=request.form["studentid"], fname=request.form["firstname"], lname=request.form["lastname"], major=request.form["studentmajor"], email=request.form["studentemail"])
        try:
            db.session.add(newstudent)
            db.session.commit()
            return render_template("roster_main.html", courseroster=Students.query.all(), courseinfo=Course.query.first())
        except:
            db.session.rollback()
            return render_template("errorpage.html", courseinfo=Course.query.first(), errormessage="Student ID already in use.  Please use a different ID.")

    elif request.form["rosterselection"]== "editstudent":
        studentid_to_edit=request.form["studentid_to_edit"]
        return render_template("editstudent.html", student=Students.query.filter_by(studentid=studentid_to_edit).first_or_404(), courseinfo=Course.query.first())

    elif request.form["rosterselection"]== "updatestudent":
        studentid_to_edit=request.form["studentid_to_edit"]
        updatestudent=Students.query.filter_by(studentid=studentid_to_edit).first()
        updatestudent.fname=request.form["firstname"]
        updatestudent.lname=request.form["lastname"]
        updatestudent.major=request.form["studentmajor"]
        updatestudent.email=request.form["studentemail"]
        db.session.commit()
        return render_template("roster_main.html", courseroster=Students.query.all(), courseinfo=Course.query.first())

    else:
        return render_template("roster_main.html", courseroster=Students.query.all(), courseinfo=Course.query.first())

@app.route('/addstudent', methods=["GET", "POST"])
def addstudent():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":
        return render_template("addstudent.html", courseinfo=Course.query.first())

    else:
        newstudent = Students(fname=request.form["firstname"], lname=request.form["lastname"], major=request.form["studentmajor"], email=request.form["studentemail"])
        db.session.add(newstudent)
        db.session.commit()
        return redirect(url_for('roster'))

@app.route('/assignments', methods=["GET", "POST"])
def assignments():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":
        return render_template("assignments.html", courseassignments=Assignments.query.all(), courseinfo=Course.query.first())

    elif request.form["assignmentselection"]== "deleteassignment":
        assignmentid_to_delete=request.form["assignmentid_to_delete"]
        Assignments.query.filter_by(assignmentid=assignmentid_to_delete).delete()
        db.session.commit()
        return render_template("assignments.html", courseassignments=Assignments.query.all(), courseinfo=Course.query.first())

    elif request.form["assignmentselection"]== "addassignment":
        newassignment = Assignments(assignmentname=request.form["assignmentname"])
        db.session.add(newassignment)
        db.session.commit()
        return render_template("assignments.html", courseassignments=Assignments.query.all(), courseinfo=Course.query.first())

    elif request.form["assignmentselection"]== "editassignment":
        assignmentid_to_edit=request.form["assignmentid_to_edit"]
        return render_template("editassignment.html", assignment=Assignments.query.filter_by(assignmentid=assignmentid_to_edit).first_or_404(), courseinfo=Course.query.first())

    elif request.form["assignmentselection"]== "updateassignment":
        assignmentid_to_edit=request.form["assignmentid_to_edit"]
        updateassignment=Assignments.query.filter_by(assignmentid=assignmentid_to_edit).first()
        updateassignment.assignmentname=request.form["assignmentname"]
        db.session.commit()
        return render_template("assignments.html", courseassignments=Assignments.query.all(), courseinfo=Course.query.first())

    else:
        return render_template("assignments.html", courseassignments=Assignments.query.all(), courseinfo=Course.query.first())

@app.route('/viewgrades', methods=["GET", "POST"])
def viewgrades():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":

        gradelist=[]
        for s in Students.query.all():
            gradetotal=0
            gradecounter=0
            studentlist=[]
            studentlist.append(s.fname)
            studentlist.append(s.lname)
            for a in Assignments.query.all():
                if Grades.query.filter_by(studentid=s.studentid, assignmentid=a.assignmentid).first():
                    currentgrade=Grades.query.filter_by(studentid=s.studentid, assignmentid=a.assignmentid).first().assignmentgrade
                    gradetotal=gradetotal+currentgrade
                    gradecounter+=1
                    studentlist.append(currentgrade)
                else:
                    studentlist.append("-")
            if gradecounter>0:
                finalgrade=gradetotal/gradecounter
                finalgrade=round(finalgrade,1)
                studentlist.append(finalgrade)
            else:
                studentlist.append("-")
            gradelist.append(studentlist)

    return render_template("viewgrades.html", assignments=Assignments.query.all(), gradelist=gradelist, courseinfo=Course.query.first())

@app.route('/viewstudent/<studid>', methods=["GET", "POST"])
def viewstudent(studid):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":

        gradelist=[]
        for a in Assignments.query.all():
            if Grades.query.filter_by(studentid=studid, assignmentid=a.assignmentid).first():
                currentgrade=Grades.query.filter_by(studentid=studid, assignmentid=a.assignmentid).first().assignmentgrade
                gradelist.append([a.assignmentid,a.assignmentname,currentgrade])
            else:
                gradelist.append([a.assignmentid,a.assignmentname,"Not Graded"])

        return render_template("viewstudent.html", student=Students.query.filter_by(studentid=studid).first(), assignments=Assignments.query.all(), gradelist=gradelist, courseinfo=Course.query.first())

    else:
        aid=request.form["assignmentnum"]
        grade=request.form["assignmentgrade"]
        sid=request.form["studentnum"]

        if Grades.query.filter_by(studentid=sid,assignmentid=aid).count():
            #merge record
            updategrade=Grades(studentid=sid,assignmentid=aid,assignmentgrade=grade)
            db.session.merge(updategrade)
            db.session.commit()
            return redirect(url_for('viewstudent',studid=sid))

        else:
            #new record
            newgrade=Grades(studentid=request.form["studentnum"],assignmentid=request.form["assignmentnum"],assignmentgrade=request.form["assignmentgrade"])
            db.session.add(newgrade)
            db.session.commit()
            return redirect(url_for('viewstudent',studid=sid))

@app.route('/viewassignment/<assignmentid>', methods=["GET", "POST"])
def viewassignment(assignmentid):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    elif request.method == "GET":

        gradelist=[]
        for a in Students.query.all():
            if Grades.query.filter_by(studentid=a.studentid, assignmentid=assignmentid).first():
                currentgrade=Grades.query.filter_by(studentid=a.studentid, assignmentid=assignmentid).first().assignmentgrade
                gradelist.append([a.studentid,a.fname,a.lname,currentgrade])
            else:
                gradelist.append([a.studentid,a.fname,a.lname,"Not Graded"])

        return render_template("viewassignment.html", assignment=Assignments.query.filter_by(assignmentid=assignmentid).first(), students=Students.query.all(), gradelist=gradelist, courseinfo=Course.query.first())

    else:
        aid=request.form["assignmentnum"]
        grade=request.form["assignmentgrade"]
        sid=request.form["studentnum"]

        if Grades.query.filter_by(studentid=sid,assignmentid=aid).count():
            #merge record
            updategrade=Grades(studentid=sid,assignmentid=aid,assignmentgrade=grade)
            db.session.merge(updategrade)
            db.session.commit()
            return redirect(url_for('viewassignment',assignmentid=aid))

        else:
            #new record
            newgrade=Grades(studentid=request.form["studentnum"],assignmentid=request.form["assignmentnum"],assignmentgrade=request.form["assignmentgrade"])
            db.session.add(newgrade)
            db.session.commit()
            return redirect(url_for('viewassignment',assignmentid=aid))

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    user = load_users(request.form["username"])
    if user is None:
        return render_template("login_page.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login_page.html", error=True)

    login_user(user)
    return redirect(url_for('index'))

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errorpage.html',errormessage="Page Not Found", courseinfo=Course.query.first())