import streamlit as st
import sqlite3
from datetime import datetime

# ---------- DATABASE ----------
conn = sqlite3.connect("astro.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    slot TEXT,
    status TEXT,
    payment TEXT,
    created_at TEXT
)
""")

conn.commit()

# ---------- DEFAULT ADMIN ----------
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users VALUES (NULL,'admin','admin123','admin')")
    conn.commit()

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------- UI ----------
st.set_page_config(page_title="Astrology Client System", layout="centered")
st.title("🔮 Astrology Client Management")
st.markdown("Developed By: Pranav Naidu | ID: 19029")

menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

# ---------- REGISTER ----------
if menu == "Register":
    st.subheader("User Registration")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Create Account"):
        cursor.execute("INSERT INTO users VALUES (NULL,?,?,?)", (u,p,"user"))
        conn.commit()
        st.success("Account created")

# ---------- LOGIN ----------
if menu == "Login":
    st.subheader("Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = cursor.fetchone()

        if user:
            st.session_state.user = user[1]
            st.session_state.role = user[3]
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

# ---------- USER DASHBOARD ----------
if st.session_state.role == "user":
    st.sidebar.success(f"User: {st.session_state.user}")

    option = st.sidebar.selectbox("User Panel", [
        "Book Slot",
        "My Bookings"
    ])

    if option == "Book Slot":
        st.subheader("Book Consultation Slot")

        slots = [
            "10:00 AM",
            "12:00 PM",
            "02:00 PM",
            "04:00 PM"
        ]

        selected = st.selectbox("Choose Slot", slots)

        cursor.execute("SELECT * FROM bookings WHERE slot=?", (selected,))
        if cursor.fetchone():
            st.error("Slot already booked ❌")
        else:
            if st.button("Pay & Book"):
                cursor.execute("""
                INSERT INTO bookings VALUES(NULL,?,?,?,?,?)
                """, (
                    st.session_state.user,
                    selected,
                    "Pending Approval",
                    "Paid",
                    str(datetime.now())
                ))
                conn.commit()
                st.success("Booking request sent")

    if option == "My Bookings":
        st.subheader("My Bookings")

        cursor.execute("SELECT * FROM bookings WHERE username=?", (st.session_state.user,))
        data = cursor.fetchall()

        for row in data:
            st.write(f"Slot: {row[2]} | Status: {row[3]} | Payment: {row[4]}")

# ---------- ADMIN DASHBOARD ----------
if st.session_state.role == "admin":
    st.sidebar.success("Admin Panel")

    option = st.sidebar.selectbox("Admin Controls", [
        "Approve Bookings",
        "View Payments",
        "Upcoming Meetings"
    ])

    if option == "Approve Bookings":
        st.subheader("Pending Bookings")

        cursor.execute("SELECT * FROM bookings WHERE status='Pending Approval'")
        data = cursor.fetchall()

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]}")
            if st.button(f"Approve {row[0]}"):
                cursor.execute("UPDATE bookings SET status='Approved' WHERE id=?", (row[0],))
                conn.commit()
                st.success("Approved")

    if option == "View Payments":
        st.subheader("Payments Received")

        cursor.execute("SELECT * FROM bookings WHERE payment='Paid'")
        data = cursor.fetchall()

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]} | Payment: {row[4]}")

    if option == "Upcoming Meetings":
        st.subheader("Approved Meetings")

        cursor.execute("SELECT * FROM bookings WHERE status='Approved'")
        data = cursor.fetchall()

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]}")