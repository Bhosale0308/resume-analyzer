
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask import redirect
import PyPDF2
import os
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
print("DB PATH:", os.getcwd())
print("FULL PATH:", os.path.abspath("data.db"))



# ✅ THEN configure database

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ Model
class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    job_role = db.Column(db.String(100))
    score = db.Column(db.Integer)
    skills_found = db.Column(db.String(200))



job_roles = {
    "python developer": ["python", "flask", "sql", "api"],
    "web developer": ["html", "css", "javascript", "react"],
    "data analyst": ["python", "sql", "excel", "pandas"]
}

def extract_text(file):
    text = ""
    try:
        pdf = PyPDF2.PdfReader(file)
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content
    except:
        return ""

    return text.lower()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    files = request.files.getlist('resumes')

    print("FILES:", files)

    if not files or files[0].filename == "":
        return "⚠️ Please select at least one file"

    job_role = request.form['job_role'].lower()
    required_skills = job_roles.get(job_role, [])

    results = []

    for file in files:
        print("Processing:", file.filename)

        text = extract_text(file)
        print("TEXT:", text[:100])

        found = []
        missing = []


        # ✅ skill loop INSIDE file loop
        for skill in required_skills:
            if skill in text:
                found.append(skill)
            else:
                missing.append(skill)

        # ✅ score INSIDE loop
        score = int((len(found) / len(required_skills)) * 100) if required_skills else 0
        resume_data = Resume(
                filename=file.filename,
                job_role=job_role,
                score=score,
                skills_found=", ".join(found)
            )

        db.session.add(resume_data)
        db.session.commit()

        # ✅ append INSIDE loop
        results.append({
            "filename": file.filename,
            "score": score,
            "found": found,
            "missing": missing
        })

    print("RESULTS:", results)

    # ✅ safety check
    if len(results) == 0:
        return "⚠️ No valid resumes processed"

    best_candidate = max(results, key=lambda x: x["score"])

    return render_template('result.html',
                           results=results,
                           best=best_candidate,
                           job_role=job_role)
@app.route('/create_db')
def create_db():
    db.create_all()
    return "Database Created!"
@app.route('/history')
def history():
    try:
        search = request.args.get('search')

        if search:
            data = Resume.query.filter(
                Resume.job_role.contains(search)
            ).all()
        else:
            data = Resume.query.all()

        return render_template('history.html', data=data)

    except Exception as e:
        return f"Error: {e}"

@app.route('/delete/<int:id>')
def delete(id):
    data = Resume.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
    return redirect('/history')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 🔥 simple login (you can upgrade later)
        if username == "admin" and password == "1234":
            return redirect('/dashboard')
        else:
            return "Invalid Login ❌"

    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    return redirect('/login')
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@app.route('/download/<int:id>')
def download(id):
    resume = Resume.query.get(id)
    if not resume:
        return "Resume not found"
    file_name = f"report_{id}.pdf"
    doc = SimpleDocTemplate(file_name)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph(f"Filename: {resume.filename}", styles['Normal']))
    content.append(Paragraph(f"Job Role: {resume.job_role}", styles['Normal']))
    content.append(Paragraph(f"Score: {resume.score}%", styles['Normal']))
    content.append(Paragraph(f"Skills: {resume.skills_found}", styles['Normal']))

    doc.build(content)

    return f"PDF Generated: {file_name}"
@app.before_first_request
def create_tables():
    db.create_all()
# with app.app_context():
#     db.create_all()
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
