import streamlit as st
import sqlite3
import hashlib
import qrcode
from io import BytesIO
from datetime import datetime
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Divine Astrology Portal", layout="centered")
st.title("🔮 Divine Astrology Consultation Portal")

DB_NAME = "astro_portal.db"
UPI_ID = "rajkumarpalanivel80@okaxis"

# ---------------- HASH FUNCTION ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- DATABASE CONNECTION ----------------
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# ---------------- CREATE TABLES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    booking_count INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    slot TEXT UNIQUE,
    amount INTEGER,
    status TEXT,
    created_at TEXT
)
""")

conn.commit()

# ---------------- CREATE ADMIN ----------------
admin_password = hash_password("admin123")
cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (username, password, role, booking_count) VALUES (?, ?, ?, ?)",
        ("admin", admin_password, "admin", 0)
    )
    conn.commit()

# ---------------- SESSION STATE ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "pending_slot" not in st.session_state:
    st.session_state.pending_slot = None

# ======================================================
# ================= AUTH SECTION =======================
# ======================================================

if not st.session_state.user:

    choice = st.radio("Select Option", ["Login", "Register"])

    # -------- REGISTER --------
    if choice == "Register":
        st.subheader("Create Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if username.strip() == "" or password.strip() == "":
                st.error("All fields required")
            else:
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    st.error("Username already exists")
                else:
                    cursor.execute(
                        "INSERT INTO users (username, password, role, booking_count) VALUES (?, ?, ?, ?)",
                        (username, hash_password(password), "user", 0)
                    )
                    conn.commit()
                    st.success("Account Created Successfully ✅")

    # -------- LOGIN --------
    if choice == "Login":
        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, hash_password(password))
            )
            user = cursor.fetchone()

            if user:
                st.session_state.user = user[1]
                st.session_state.role = user[3]
                st.rerun()
            else:
                st.error("Invalid Credentials ❌")

# ======================================================
# ================= USER DASHBOARD =====================
# ======================================================

if st.session_state.role == "user":

    st.success(f"Welcome {st.session_state.user} 👋")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.session_state.pending_slot = None
        st.rerun()

    slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]

    cursor.execute(
        "SELECT booking_count FROM users WHERE username=?",
        (st.session_state.user,)
    )
    count = cursor.fetchone()[0]

    amount = 501 if count == 0 else 301
    st.write(f"Consultation Fee: ₹{amount}")

    selected_slot = st.selectbox("Choose Slot", slots)

    if st.button("Generate Payment QR"):
        cursor.execute("SELECT * FROM bookings WHERE slot=?", (selected_slot,))
        if cursor.fetchone():
            st.error("Slot already booked ❌")
        else:
            st.session_state.pending_slot = selected_slot

    # -------- SHOW QR --------
    if st.session_state.pending_slot:

        upi_link = f"upi://pay?pa={UPI_ID}&pn=Astrology&am={amount}&cu=INR"

        qr = qrcode.make(upi_link)
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)

        st.image(buffer, caption="Scan & Pay Using Any UPI App")
        st.info("After payment click below button")

        if st.button("I Have Paid"):

            cursor.execute(
                "INSERT INTO bookings (username, slot, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (st.session_state.user, st.session_state.pending_slot, amount, "Pending", str(datetime.now()))
            )

            cursor.execute(
                "UPDATE users SET booking_count = booking_count + 1 WHERE username=?",
                (st.session_state.user,)
            )

            conn.commit()

            st.success("Payment Submitted! Waiting for Admin Approval.")
            st.session_state.pending_slot = None
            st.rerun()

    # -------- MY BOOKINGS --------
    st.subheader("My Bookings")

    cursor.execute(
        "SELECT slot, amount, status FROM bookings WHERE username=?",
        (st.session_state.user,)
    )

    bookings = cursor.fetchall()

    if bookings:
        for row in bookings:
            st.write(f"{row[0]} | ₹{row[1]} | {row[2]}")
    else:
        st.info("No bookings yet.")

# ======================================================
# ================= ADMIN DASHBOARD ====================
# ======================================================

if st.session_state.role == "admin":

    st.success("Admin Dashboard 👑")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

    st.subheader("Pending Bookings")

    cursor.execute("SELECT id, username, slot, amount FROM bookings WHERE status='Pending'")
    pending = cursor.fetchall()

    if pending:
        for row in pending:
            st.write(f"{row[1]} | {row[2]} | ₹{row[3]}")
            if st.button("Approve " + str(row[0])):
                cursor.execute(
                    "UPDATE bookings SET status='Approved' WHERE id=?",
                    (row[0],)
                )
                conn.commit()
                st.rerun()
    else:
        st.info("No pending bookings.")

    st.subheader("Total Revenue")

    cursor.execute("SELECT amount FROM bookings WHERE status='Approved'")
    total = sum([r[0] for r in cursor.fetchall()])
    st.write(f"₹{total}")
