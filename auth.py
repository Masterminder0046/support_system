from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ticket_logger import get_db_connection

auth_bp = Blueprint("auth", __name__)

# 📝 Signup
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("⚠️ Email already registered.")
                return redirect(url_for("auth.signup"))
            hash_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hash_pw))
            conn.commit()
            flash("🎉 Signup successful. Please log in.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"❌ Signup error: {e}")
            return redirect(url_for("auth.signup"))
        finally:
            conn.close()
    return render_template("signup.html")

# 🔐 Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["email"] = user["email"]
                session["name"] = user.get("name", "admin")  # Optional if name column exists
                flash("✅ Logged in successfully.")
                return redirect(url_for("dashboard"))
            flash("❌ Invalid credentials.")
        except Exception as e:
            flash(f"❌ Login error: {e}")
        finally:
            conn.close()
    return render_template("login.html")

# 🚪 Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("👋 Logged out.")
    return redirect(url_for("auth.login"))
