import os
import logging
import csv
import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, LOG_FILE, LOG_LEVEL
from deep_translator import GoogleTranslator
from datetime import datetime

LOG_INITIALIZED = False

def setup_logging():
    global LOG_INITIALIZED
    if LOG_INITIALIZED:
        return
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'
    )
    console = logging.StreamHandler()
    console.setLevel(LOG_LEVEL)
    console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logging.getLogger().addHandler(console)
    LOG_INITIALIZED = True

def get_db_connection():
    try:
        print("🔧 Attempting DB connection...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=5,
            use_pure=True,
            auth_plugin='mysql_native_password'
        )
        print("✅ DB connection successful.")
        return conn
    except mysql.connector.Error as err:
        print("❌ MySQL error:", err)
    except Exception as e:
        print("❌ General error:", type(e).__name__, "-", e)
    return None


# -------------------------
# Ticket operations
# -------------------------
def log_ticket(email, subject, message, issue_type):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting log_ticket.")
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM tickets WHERE email = %s", (email,))
        existing = cursor.fetchone()
        if existing:
            logging.warning(f"Duplicate ticket attempt from {email}")
            return None  # Or return existing['id'] if you want to redirect
        cursor.execute("""
            INSERT INTO tickets (email, subject, message, issue_type)
            VALUES (%s, %s, %s, %s)
        """, (email, subject, message, issue_type))
        conn.commit()
        ticket_id = cursor.lastrowid
        logging.info(f"Ticket logged: {email} | {issue_type} | {subject}")
        return ticket_id
    except Exception as e:
        logging.error(f"Failed to log ticket: {e}")
        return None
    finally:
        conn.close()


def update_ticket_status(ticket_id, new_status):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting update_ticket_status.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets
            SET status = %s,
                closed_at = CASE WHEN %s = 'closed' THEN NOW() ELSE closed_at END
            WHERE id = %s
        """, (new_status, new_status, ticket_id))
        if new_status == "closed":
            cursor.execute("UPDATE tickets SET ack_sent = 0 WHERE id = %s", (ticket_id,))
        conn.commit()
        logging.info(f"Ticket {ticket_id} updated to status: {new_status}")
    except Exception as e:
        logging.error(f"Failed to update status for ticket {ticket_id}: {e}")
    finally:
        conn.close()

def delete_ticket(ticket_id):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting delete_ticket.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
        conn.commit()
        logging.info(f"Deleted ticket: {ticket_id}")
    except Exception as e:
        logging.error(f"Failed to delete ticket {ticket_id}: {e}")
    finally:
        conn.close()

def get_ticket(ticket_id):
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting get_ticket.")
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        ticket = cursor.fetchone()
        return ticket
    except Exception as e:
        logging.error(f"Failed to fetch ticket {ticket_id}: {e}")
        return None
    finally:
        conn.close()

def get_all_tickets(category=None):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting get_all_tickets.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if category:
            cursor.execute("SELECT * FROM tickets WHERE issue_type = %s ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to retrieve tickets: {e}")
        return []
    finally:
        conn.close()

def export_tickets_to_csv(filename):
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting export_tickets_to_csv.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets")
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        logging.info(f"Exported tickets to {filename}")
    except Exception as e:
        logging.error(f"Failed to export tickets: {e}")
    finally:
        conn.close()

# -------------------------
# Replies
# -------------------------
def log_admin_reply(ticket_id, reply_text):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting log_admin_reply.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO replies (ticket_id, reply_text, timestamp)
            VALUES (%s, %s, %s)
        """, (ticket_id, reply_text, datetime.now()))
        conn.commit()
        logging.info(f"Reply logged for ticket {ticket_id}")
    except Exception as e:
        logging.error(f"Failed to log reply for ticket {ticket_id}: {e}")
    finally:
        conn.close()

def get_replies(ticket_id):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting get_replies.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM replies WHERE ticket_id = %s ORDER BY timestamp ASC", (ticket_id,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to retrieve replies for ticket {ticket_id}: {e}")
        return []
    finally:
        conn.close()

# -------------------------
# Notes
# -------------------------
def add_note(ticket_id, author, content):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting add_note.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notes (ticket_id, author, content)
            VALUES (%s, %s, %s)
        """, (ticket_id, author, content))
        conn.commit()
        logging.info(f"Note added to ticket {ticket_id} by {author}")
    except Exception as e:
        logging.error(f"Failed to add note to ticket {ticket_id}: {e}")
    finally:
        conn.close()

def get_notes(ticket_id):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting get_notes.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM notes WHERE ticket_id = %s ORDER BY timestamp ASC", (ticket_id,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to retrieve notes for ticket {ticket_id}: {e}")
        return []
    finally:
        conn.close()

# -------------------------
# Tasks
# -------------------------
def add_task(ticket_id, assigned_to, description, due_date):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting add_task.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (ticket_id, assigned_to, description, due_date)
            VALUES (%s, %s, %s, %s)
        """, (ticket_id, assigned_to, description, due_date))
        conn.commit()
        logging.info(f"Task assigned to {assigned_to} for ticket {ticket_id}")
    except Exception as e:
        logging.error(f"Failed to add task to ticket {ticket_id}: {e}")
    finally:
        conn.close()

def get_tasks(ticket_id):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting get_tasks.")
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE ticket_id = %s ORDER BY due_date ASC", (ticket_id,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to retrieve tasks for ticket {ticket_id}: {e}")
        return []
    finally:
        conn.close()

def update_task_status(task_id, new_status):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting update_task_status.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (new_status, task_id))
        conn.commit()
        logging.info(f"Task {task_id} updated to status: {new_status}")
    except Exception as e:
        logging.error(f"Failed to update task {task_id}: {e}")
    finally:
        conn.close()

# -------------------------
# Helpers
# -------------------------
def close_ticket(ticket_id):
    setup_logging()
    conn = get_db_connection()
    if not conn:
        logging.error("DB connection failed. Aborting close_ticket.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets
            SET status = 'closed',
                closed_at = NOW(),
                ack_sent = 0
            WHERE id = %s
        """, (ticket_id,))
        conn.commit()
        logging.info(f"Ticket {ticket_id} closed.")
    except Exception as e:
        logging.error(f"Failed to close ticket {ticket_id}: {e}")
    finally:
        conn.close()

# -------------------------
# Translation
# -------------------------
def translate_text(text, target_lang='ta'):
    setup_logging()
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        logging.error(f"Translation failed: {e}")
        return "Translation error"
