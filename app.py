import streamlit as st
import sqlite3
import hashlib
import qrcode
from datetime import datetime
from io import BytesIO

# ---------- HASH FUNCTION ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- DATABASE ----------
conn = sqlite3.connect("astro.db", check_same_thread=False)
cursor = conn.cursor()

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

# ---------- CREATE ADMIN ----------
admin_password = hash_password("admin123")

cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO users (username, password, role, booking_count) VALUES (?, ?, ?, ?)",
        ("admin", admin_password, "admin", 0)
    )
    conn.commit()

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None

if "role" not in st.session_state:
    st.session_state.role = None

# ---------- PAGE ----------
st.set_page_config(page_title="Divine Astrology Portal")
st.title("Divine Astrology Consultation Portal")

UPI_ID = "rajkumarpalanivel80@okaxis"

# ---------- LOGOUT ----------
if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.experimental_rerun()

# ---------- AUTH ----------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    if menu == "Register":
        st.subheader("Register")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Create Account"):
            try:
                cursor.execute(
                    "INSERT INTO users (username, password, role, booking_count) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), "user", 0)
                )
                conn.commit()
                st.success("Account Created")
            except:
                st.error("Username already exists")

    if menu == "Login":
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
                st.experimental_rerun()
            else:
                st.error("Invalid Credentials")

# ---------- USER DASHBOARD ----------
if st.session_state.role == "user":

    st.sidebar.success("User: " + st.session_state.user)

    option = st.sidebar.selectbox("User Panel", ["Book Slot", "My Bookings"])

    slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]

    if option == "Book Slot":

        cursor.execute(
            "SELECT booking_count FROM users WHERE username=?",
            (st.session_state.user,)
        )
        booking_count = cursor.fetchone()[0]

        amount = 501 if booking_count == 0 else 301

        st.write("Consultation Fee:", amount)

        for slot in slots:
            cursor.execute("SELECT * FROM bookings WHERE slot=?", (slot,))
            booked = cursor.fetchone()

            if booked:
                st.write(slot + " - Booked")
            else:
                if st.button("Book " + slot):

                    upi_link = "upi://pay?pa=" + UPI_ID + "&pn=Astrology&am=" + str(amount) + "&cu=INR"

                    qr = qrcode.make(upi_link)
                    buffer = BytesIO()
                    qr.save(buffer)
                    buffer.seek(0)

                    st.image(buffer)

                    if st.button("Confirm Payment"):

                        cursor.execute(
                            "INSERT INTO bookings (username, slot, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
                            (st.session_state.user, slot, amount, "Pending", str(datetime.now()))
                        )

                        cursor.execute(
                            "UPDATE users SET booking_count = booking_count + 1 WHERE username=?",
                            (st.session_state.user,)
                        )

                        conn.commit()
                        st.success("Booking Request Sent")
                        st.experimental_rerun()

    if option == "My Bookings":

        cursor.execute(
            "SELECT * FROM bookings WHERE username=?",
            (st.session_state.user,)
        )
        data = cursor.fetchall()

        for row in data:
            st.write("Slot:", row[2])
            st.write("Amount:", row[3])
            st.write("Status:", row[4])
            st.write("-----")

# ---------- ADMIN DASHBOARD ----------
if st.session_state.role == "admin":

    st.sidebar.success("Admin Panel")

    option = st.sidebar.selectbox(
        "Admin Controls",
        ["Approve Bookings", "View Payments", "Approved Meetings"]
    )

    if option == "Approve Bookings":

        cursor.execute("SELECT * FROM bookings WHERE status='Pending'")
        pending = cursor.fetchall()

        for row in pending:
            st.write("User:", row[1], "Slot:", row[2], "Amount:", row[3])
            if st.button("Approve " + str(row[0])):
                cursor.execute(
                    "UPDATE bookings SET status='Approved' WHERE id=?",
                    (row[0],)
                )
                conn.commit()
                st.experimental_rerun()

    if option == "View Payments":

        cursor.execute("SELECT * FROM bookings")
        all_bookings = cursor.fetchall()

        total = sum([row[3] for row in all_bookings])
        st.write("Total Revenue:", total)

        for row in all_bookings:
            st.write(row[1], row[2], row[3])

    if option == "Approved Meetings":

        cursor.execute("SELECT * FROM bookings WHERE status='Approved'")
        approved = cursor.fetchall()

        for row in approved:
            st.write(row[1], "-", row[2], "-", row[3])

                            
