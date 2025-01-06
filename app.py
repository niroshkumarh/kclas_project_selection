from flask import Flask, render_template, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import csv
from datetime import datetime
from io import StringIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///registrations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models for Registration and Projects
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    roll_number = db.Column(db.String(100))
    department = db.Column(db.String(100))
    project = db.Column(db.String(100))
    contact_number = db.Column(db.String(100))
    kclas_email = db.Column(db.String(100))
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add timestamp

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    student_limit = db.Column(db.Integer)
    current_count = db.Column(db.Integer, default=0)

# Initialize the database and projects manually after app is created
def initialize_projects():
    projects = [
        {"name": "Child Nutrition", "student_limit": 1},
        {"name": "Non Communicable Disease (NCD)", "student_limit": 70},
        {"name": "Child Safety and Protection", "student_limit": 70},
        {"name": "Learning Achievement", "student_limit": 70},
        {"name": "Substance Abuse", "student_limit": 70},
        {"name": "Youth Empowerment", "student_limit": 70},
    ]
    
    for project in projects:
        if not Project.query.filter_by(name=project["name"]).first():
            new_project = Project(
                name=project["name"],
                student_limit=project["student_limit"]
            )
            db.session.add(new_project)
    
    db.session.commit()

@app.route("/check_email", methods=["POST"])
def check_email():
    email = request.form["email"]
    # Check if the email already exists in the database
    existing_user = Registration.query.filter_by(kclas_email=email).first()
    if existing_user:
        return jsonify({"exists": True})
    return jsonify({"exists": False})

# Routes
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        roll_number = request.form["roll_number"]
        department = request.form["department"]
        project_name = request.form["project"]
        contact_number = request.form["contact_number"]
        kclas_email = request.form["kclas_email"]
        reason = request.form["reason"]

        try:
            db.session.begin()
            project_obj = Project.query.filter_by(name=project_name).first()

            if project_obj and project_obj.current_count < project_obj.student_limit:
                new_registration = Registration(
                    name=name,
                    roll_number=roll_number,
                    department=department,
                    project=project_name,
                    contact_number=contact_number,
                    kclas_email=kclas_email,
                    reason=reason
                )
                db.session.add(new_registration)
                project_obj.current_count += 1
                db.session.commit()

                # Return success message
                return jsonify({"success": True, "message": "Your registration was successful!"})

            else:
                # Return error message if project is full
                return jsonify({"success": False, "message": "Project is full or unavailable"})

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": "An error occurred. Please try again later."})

    projects = Project.query.all()
    return render_template("register.html", projects=projects)

@app.route("/admin")
def admin():
    registrations = Registration.query.all()
    project_counts = {project.name: project.current_count for project in Project.query.all()}
    return render_template("admin.html", registrations=registrations, project_counts=project_counts)

@app.route("/download_csv")
def download_csv():
    # Fetch all registrations from the database
    registrations = Registration.query.all()

    # Create the CSV response
    def generate_csv():
        # Create a StringIO object to hold the CSV data
        output = StringIO()
        csv_writer = csv.writer(output)
        
        # Write the header row
        csv_writer.writerow(['ID', 'Name', 'Roll Number', 'Department', 'Project', 'Contact', 'Email', 'Reason', 'Timestamp'])

        # Write the registration data
        for reg in registrations:
            csv_writer.writerow([reg.id, reg.name, reg.roll_number, reg.department, reg.project,
                                 reg.contact_number, reg.kclas_email, reg.reason, reg.timestamp])

        output.seek(0)  # Go back to the start of the StringIO object so it can be read
        return output.getvalue()

    return Response(generate_csv(), content_type='text/csv', headers={"Content-Disposition": "attachment;filename=registrations.csv"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create the tables if they don't exist
        initialize_projects()  # Initialize projects manually

    # Explicitly set host and port
    app.run(host="0.0.0.0", port=5123, debug=True)
