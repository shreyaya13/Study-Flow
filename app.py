import os, sqlite3, math
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-deployment")
DB_PATH = os.path.join(os.path.dirname(__file__), "studyflow.db")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None: conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        name TEXT NOT NULL, color TEXT NOT NULL DEFAULT '#7667e8',
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, name)
    );
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        subject_id INTEGER, question TEXT NOT NULL, answer TEXT NOT NULL,
        repetitions INTEGER NOT NULL DEFAULT 0, interval_days INTEGER NOT NULL DEFAULT 0,
        ease REAL NOT NULL DEFAULT 2.5, due_date TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        subject_id INTEGER, duration_minutes INTEGER NOT NULL,
        completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    );
    """)
    conn.commit(); conn.close()

init_db()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_user():
    user = None
    if session.get("user_id"):
        user = db().execute("SELECT id,name,email FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return {"current_user": user}

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        if not name or not email or len(password)<8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
        else:
            try:
                cur=db().execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                    (name,email,generate_password_hash(password)))
                db().commit(); session.clear(); session["user_id"]=cur.lastrowid
                flash("Your account is ready. Welcome to StudyFlow!", "success")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "error")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        user=db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password","")):
            session.clear(); session["user_id"]=user["id"]
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    uid=session["user_id"]; today=date.today().isoformat()
    conn=db()
    subjects=conn.execute("SELECT s.*, (SELECT COUNT(*) FROM cards c WHERE c.subject_id=s.id) card_count FROM subjects s WHERE s.user_id=? ORDER BY s.name",(uid,)).fetchall()
    total=conn.execute("SELECT COUNT(*) FROM cards WHERE user_id=?",(uid,)).fetchone()[0]
    due=conn.execute("SELECT COUNT(*) FROM cards WHERE user_id=? AND due_date<=?",(uid,today)).fetchone()[0]
    minutes=conn.execute("SELECT COALESCE(SUM(duration_minutes),0) FROM sessions WHERE user_id=? AND date(completed_at)=?",(uid,today)).fetchone()[0]
    sessions=conn.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY completed_at DESC LIMIT 5",(uid,)).fetchall()
    weekly=conn.execute("""SELECT date(completed_at) day, SUM(duration_minutes) minutes FROM sessions
        WHERE user_id=? AND date(completed_at)>=date('now','-6 day') GROUP BY date(completed_at)""",(uid,)).fetchall()
    weekmap={r["day"]:r["minutes"] for r in weekly}
    week=[{"day":(date.today()-timedelta(days=i)).strftime("%a"),"minutes":weekmap.get((date.today()-timedelta(days=i)).isoformat(),0)} for i in range(6,-1,-1)]
    return render_template("dashboard.html", subjects=subjects,total=total,due=due,minutes=minutes,sessions=sessions,week=week)

@app.route("/subjects", methods=["GET","POST"])
@login_required
def subjects():
    uid=session["user_id"]
    if request.method=="POST":
        name=request.form.get("name","").strip()
        color=request.form.get("color","#7667e8")
        if name:
            try:
                db().execute("INSERT INTO subjects(user_id,name,color) VALUES(?,?,?)",(uid,name,color)); db().commit()
                flash("Subject added.", "success")
            except sqlite3.IntegrityError: flash("That subject already exists.", "error")
        return redirect(url_for("subjects"))
    rows=db().execute("""SELECT s.*,COUNT(c.id) card_count FROM subjects s LEFT JOIN cards c ON c.subject_id=s.id
        WHERE s.user_id=? GROUP BY s.id ORDER BY s.name""",(uid,)).fetchall()
    return render_template("subjects.html",subjects=rows)

@app.route("/subjects/<int:sid>/delete",methods=["POST"])
@login_required
def delete_subject(sid):
    db().execute("DELETE FROM subjects WHERE id=? AND user_id=?",(sid,session["user_id"])); db().commit()
    flash("Subject deleted. Its flashcards were kept without a subject.", "success")
    return redirect(url_for("subjects"))

@app.route("/cards")
@login_required
def cards():
    uid=session["user_id"]
    rows=db().execute("""SELECT c.*,s.name subject_name,s.color FROM cards c LEFT JOIN subjects s ON s.id=c.subject_id
        WHERE c.user_id=? ORDER BY c.created_at DESC""",(uid,)).fetchall()
    subjects=db().execute("SELECT * FROM subjects WHERE user_id=? ORDER BY name",(uid,)).fetchall()
    return render_template("cards.html",cards=rows,subjects=subjects)

@app.route("/cards/new",methods=["GET","POST"])
@app.route("/cards/<int:cid>/edit",methods=["GET","POST"])
@login_required
def card_form(cid=None):
    uid=session["user_id"]; card=None
    if cid:
        card=db().execute("SELECT * FROM cards WHERE id=? AND user_id=?",(cid,uid)).fetchone()
        if not card: return redirect(url_for("cards"))
    subjects=db().execute("SELECT * FROM subjects WHERE user_id=? ORDER BY name",(uid,)).fetchall()
    if request.method=="POST":
        question=request.form.get("question","").strip(); answer=request.form.get("answer","").strip()
        sid=request.form.get("subject_id") or None
        if not question or not answer:
            flash("Both question and answer are required.", "error")
        else:
            if sid:
                valid=db().execute("SELECT id FROM subjects WHERE id=? AND user_id=?",(sid,uid)).fetchone()
                if not valid: sid=None
            if card:
                db().execute("UPDATE cards SET question=?,answer=?,subject_id=? WHERE id=? AND user_id=?",(question,answer,sid,cid,uid))
                flash("Flashcard updated.", "success")
            else:
                db().execute("INSERT INTO cards(user_id,subject_id,question,answer,due_date) VALUES(?,?,?,?,?)",(uid,sid,question,answer,date.today().isoformat()))
                flash("Flashcard created.", "success")
            db().commit(); return redirect(url_for("cards"))
    return render_template("card_form.html",card=card,subjects=subjects)

@app.route("/cards/<int:cid>/delete",methods=["POST"])
@login_required
def delete_card(cid):
    db().execute("DELETE FROM cards WHERE id=? AND user_id=?",(cid,session["user_id"])); db().commit()
    flash("Flashcard deleted.", "success"); return redirect(url_for("cards"))

@app.route("/practice")
@login_required
def practice():
    uid=session["user_id"]
    rows=db().execute("""SELECT c.*,s.name subject_name FROM cards c LEFT JOIN subjects s ON s.id=c.subject_id
        WHERE c.user_id=? AND c.due_date<=? ORDER BY c.due_date,c.id""",(uid,date.today().isoformat())).fetchall()
    return render_template("practice.html",cards=rows)

@app.route("/review/<int:cid>",methods=["POST"])
@login_required
def review(cid):
    uid=session["user_id"]; quality=max(0,min(5,int(request.form.get("quality",3))))
    card=db().execute("SELECT * FROM cards WHERE id=? AND user_id=?",(cid,uid)).fetchone()
    if not card: return redirect(url_for("practice"))
    reps=card["repetitions"]; interval=card["interval_days"]; ease=card["ease"]
    if quality < 3:
        reps=0; interval=1
    else:
        if reps==0: interval=1
        elif reps==1: interval=6
        else: interval=max(1,round(interval*ease))
        reps+=1
    ease=max(1.3,ease + (0.1-(5-quality)*(0.08+(5-quality)*0.02)))
    due=(date.today()+timedelta(days=interval)).isoformat()
    db().execute("UPDATE cards SET repetitions=?,interval_days=?,ease=?,due_date=? WHERE id=?",
        (reps,interval,ease,due,cid)); db().commit()
    return redirect(url_for("practice"))

@app.route("/sessions",methods=["POST"])
@login_required
def save_session():
    try: minutes=max(1,min(600,int(request.form.get("minutes",25))))
    except ValueError: minutes=25
    sid=request.form.get("subject_id") or None
    if sid:
        valid=db().execute("SELECT id FROM subjects WHERE id=? AND user_id=?",(sid,session["user_id"])).fetchone()
        if not valid: sid=None
    db().execute("INSERT INTO sessions(user_id,subject_id,duration_minutes) VALUES(?,?,?)",(session["user_id"],sid,minutes))
    db().commit(); flash(f"Great work! {minutes} focus minutes saved.", "success")
    return redirect(url_for("dashboard"))



@app.context_processor
def inject_dates():
    return {"now_date": date.today().isoformat(), "now_label": date.today().strftime("%A, %d %B %Y")}

if __name__ == "__main__":
    app.run(debug=True)
