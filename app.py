import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from config import SECRET_KEY
from ticket_logger import (
    log_ticket, update_ticket_status, delete_ticket,
    add_note, get_notes, add_task, get_tasks, update_task_status,
    translate_text, get_ticket, log_admin_reply, get_replies,
    export_tickets_to_csv, get_all_tickets
)
from email_utils import send_email, fetch_emails
from werkzeug.security import generate_password_hash, check_password_hash
from auth import auth_bp
import mysql.connector

# 🚀 App setup
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(auth_bp)

# 📦 Database connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sheik@2005",
        database="supportuser"
    )

# 🔐 Login protection
@app.before_request
def require_login():
    public_routes = ["auth.login", "auth.signup", "static"]
    if request.endpoint not in public_routes and not session.get("user_id"):
        return redirect(url_for("auth.login"))

# 🏁 Landing page
@app.route("/")
def home():
    return redirect("/dashboard")

# 📊 Dashboard
@app.route("/dashboard")
def dashboard():
    category = request.args.get("category")
    tickets = get_all_tickets(category)
    enriched = []
    for ticket in tickets:
        ticket_id = ticket['id']
        ticket['replies'] = get_replies(ticket_id)
        ticket['notes'] = get_notes(ticket_id)
        ticket['tasks'] = get_tasks(ticket_id)
        enriched.append(ticket)
    return render_template("dashboard.html", tickets=enriched, selected_category=category)

# 📄 View ticket
@app.route("/ticket/<int:ticket_id>")
def view_ticket(ticket_id):
    ticket = get_ticket(ticket_id)
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for("dashboard"))
    notes = get_notes(ticket_id)
    tasks = get_tasks(ticket_id)
    replies = get_replies(ticket_id)
    return render_template("ticket_detail.html", ticket=ticket, notes=notes, tasks=tasks, replies=replies)

# 📝 Add note
@app.route("/ticket/<int:ticket_id>/note", methods=["POST"])
def add_internal_note(ticket_id):
    author = session.get("name", "admin")
    content = request.form["content"]
    add_note(ticket_id, author, content)
    flash("Note added.", "info")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))

# 📋 Assign task
@app.route("/ticket/<int:ticket_id>/task", methods=["POST"])
def add_internal_task(ticket_id):
    assigned_to = request.form.get("assigned_to", "admin")
    description = request.form["description"]
    due_date = request.form["due_date"]
    add_task(ticket_id, assigned_to, description, due_date)
    flash("Task assigned.", "info")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))

# ✅ Update task
@app.route("/task/<int:task_id>/update", methods=["POST"])
def update_task(task_id):
    new_status = request.form["status"]
    update_task_status(task_id, new_status)
    flash(f"Task updated to {new_status}.", "info")
    return redirect(request.referrer or url_for("dashboard"))

# 🔄 Update ticket
@app.route("/update_status/<int:ticket_id>", methods=["POST"])
def update_status(ticket_id):
    new_status = request.form["status"]
    update_ticket_status(ticket_id, new_status)
    flash(f"Ticket #{ticket_id} updated to {new_status}.", "info")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))

# 📧 Admin reply
@app.route("/admin_reply/<int:ticket_id>", methods=["POST"])
def admin_reply(ticket_id):
    reply_text = request.form["reply_text"]
    ticket = get_ticket(ticket_id)
    if not ticket:
        flash("Ticket not found.", "danger")
        return redirect(url_for("dashboard"))
    try:
        success = send_email(to=ticket["email"], subject=f"Re: {ticket['subject']}", body=reply_text)
        if success:
            log_admin_reply(ticket_id, reply_text)
            flash("Reply sent.", "success")
        else:
            flash("Failed to send email.", "danger")
    except Exception as e:
        logging.error(f"Reply failed: {e}")
        flash("Error sending reply.", "danger")
    return redirect(url_for("view_ticket", ticket_id=ticket_id))

# 🌐 Translate
@app.route("/translate", methods=["POST"])
def translate():
    text = request.form["text"]
    target_lang = request.form["lang"]
    translated = translate_text(text, target_lang)
    return jsonify({"translated": translated})

# 📤 Export CSV
@app.route("/export_csv", methods=["POST"])
def export_csv():
    filepath = "exports/tickets_export.csv"
    os.makedirs("exports", exist_ok=True)
    export_tickets_to_csv(filepath)
    flash("Tickets exported to CSV.", "info")
    return redirect(url_for("dashboard"))

# 📥 Fetch emails
@app.route("/fetch_emails")
def fetch_emails_route():
    fetch_emails()
    flash("New emails fetched and tickets updated.", "info")
    return redirect(url_for("dashboard"))

# ❌ Delete ticket
@app.route("/delete_ticket", methods=["POST"])
def delete_ticket_route():
    ticket_id = request.form.get("ticket_id")
    if ticket_id:
        delete_ticket(ticket_id)
    return redirect("/dashboard")

# 🧪 Healthcheck
@app.route("/healthcheck")
def healthcheck():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tickets")
        count = cursor.fetchone()[0]
        return jsonify({"status": "ok", "tickets": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# 🚀 Run
if __name__ == "__main__":
    app.run(debug=True)
