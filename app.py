import streamlit as st
import sqlite3
import hashlib
import qrcode
from datetime import datetime
from io import BytesIO

# ---------------- PASSWORD HASH FUNCTION ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- DATABASE CONNECTION ----------------
conn = sqlite3.connect("astro.db", check_same_thread=False)
cursor = conn.cursor()

# USERS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    booking_count INTEGER DEFAULT 0
)
""")

# BOOKINGS TABLE
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

# ---------------- CREATE DEFAULT ADMIN ----------------
admin_password = hash_password("admin123")

cursor.execute("SELECT * FROM users WHERE username='admin'")
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

# ---------------- UI DESIGN ----------------
st.set_page_config(page_title="Divine Astrology Portal", layout="centered")

st.markdown("""
<style>
body {
    background-color: #0e0e0e;
}
h1, h2, h3 {
    color: #d4af37;
}
.stButton>button {
    background-color: #d4af37;
    color: black;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔱 Divine Astrology Consultation Portal 🔱")
st.markdown("### Blessings & Guidance Awaits You ✨")

UPI_ID = "rajkumarpalanivel80@okaxis"

# ---------------- LOGOUT ----------------
if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# ---------------- AUTH SECTION ----------------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    # REGISTER
    if menu == "Register":
        st.subheader("Create Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                cursor.execute(
                    "INSERT INTO users (username, password, role, booking_count) VALUES (?, ?, ?, ?)",
                    (username, hash_password(password), "user", 0)
                )
                conn.commit()
                st.success("Account Created Successfully 🙏")
            except:
                st.error("Username already exists")

    # LOGIN
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
                st.success("Login Successful 🙏")
                st.rerun()
            else:
                st.error("Invalid Credentials")

# ---------------- USER DASHBOARD ----------------
if st.session_state.role == "user":

    st.sidebar.success(f"Welcome {st.session_state.user}")

    user_option = st.sidebar.selectbox("User Panel", ["Book Slot", "My Bookings"])

    slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]

    # BOOK SLOT
    if user_option == "Book Slot":

        st.subheader("Available Divine Slots")

        cursor.execute(
            "SELECT booking_count FROM users WHERE username=?",
            (st.session_state.user,)
        )
        booking_count = cursor.fetchone()[0]

        amount = 501 if booking_count == 0 else 301
        st.info(f"Consultation Fee: ₹{amount}")

        for slot in slots:
            cursor.execute("SELECT * FROM bookings WHERE slot=?", (slot,))
            booked = cursor.fetchone()

            if booked:
                st.error(f"{slot} - Booked ❌")
            else:
                if st.button(f"Book {slot}"):

                    upi_link = f"upi://pay?pa={UPI_ID}&pn=AstrologyConsultation&am={amount}&cu=INR"

                    qr = qrcode.make(upi_link)
                    buffer = BytesIO()
                    qr.save(buffer)
                    buffer.seek(0)

                    st.image(buffer, caption=f"Scan to Pay ₹{amount}")

                    if st.button("Confirm Payment"):
                        cursor.execute(
                            "INSERT INTO bookings (username, slot, amount, status, created_at) VALUES (?, ?, ?, ?, ?)",
                            (st.session_state.user, slot, amount, "Pending Approval", str(datetime.now()))
                        )

                        cursor.execute(
                            "UPDATE users SET booking_count = booking_count + 1 WHERE username=?",
                            (st.session_state.user,)
                        )

                        conn.commit()
                        st.success("Booking Request Sent 🙏 Await Admin Approval")
                        st.rerun()

    # MY BOOKINGS
    if user_option == "My Bookings":

        st.subheader("Your Consultations")

        cursor.execute(
            "SELECT * FROM bookings WHERE username=?",
            (st.session_state.user,)
        )
        bookings = cursor.fetchall()

        if not bookings:
            st.info("No bookings yet")

        for row in bookings:
            st.write(f"🕒 Slot: {row[2]}")
            st.write(f"💰 Amount: ₹{row[3]}")
            st.write(f"📌 Status: {row[4]}")
            st.write("---")

# ---------------- ADMIN DASHBOARD ----------------
if st.session_state.role == "admin":

    st.sidebar.success("Admin Panel 🔱")

    admin_option = st.sidebar.selectbox(
        "Admin Controls",
        ["Approve Bookings", "View Payments", "Upcoming Meetings"]
    )

    # APPROVE BOOKINGS
    if admin_option == "Approve Bookings":

        st.subheader("Pending Approval")

        cursor.execute("SELECT * FROM bookings WHERE status='Pending Approval'")
        pending = cursor.fetchall()

        if not pending:
            st.info("No Pending Bookings")

        for row in pending:
            st.write(f"User: {row[1]} | Slot: {row[2]} | ₹{row[3]}")
            if st.button(f"Approve {row[0]}"):
                cursor.execute(
                    "UPDATE bookings SET status='Approved' WHERE id=?",
                    (row[0],)
                )
                conn.commit()
                st.success("Approved ✅")
                st.rerun()

    # VIEW PAYMENTS
    if admin_option == "View Payments":

        st.subheader("Payments Received")

        cursor.execute("SELECT * FROM bookings")
        all_bookings = cursor.fetchall()

        total = sum([row[3] for row in all_bookings])
        st.success(f"Total Revenue: ₹{total}")

        for row in all_bookings:
            st.write(f"{row[1]} | {row[2]} | ₹{row[3]}")

    # UPCOMING MEETINGS
    if admin_option == "Upcoming Meetings":

        st.subheader("Approved Consultations")

        cursor.execute("SELECT * FROM bookings WHERE status='Approved'")
        approved = cursor.fetchall()

        if not approved:
            st.info("No Approved Meetings")

        for row in approved:
            st.write(f"{row[1]} - {row[2]} - ₹{row[3]}")conn.commit()

# ---------------- CREATE ADMIN ----------------
admin_password = hash_password("admin123")

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users VALUES (NULL,?,?,?,?)",
                   ("admin", admin_password, "admin", 0))
    conn.commit()

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------------- SPIRITUAL UI ----------------
st.set_page_config(page_title="Divine Astrology Portal", layout="centered")

st.markdown("""
<style>
body {
    background-color: #0e0e0e;
}
h1, h2, h3 {
    color: #d4af37;
}
.stButton>button {
    background-color: #d4af37;
    color: black;
    border-radius: 8px;
}
.stSidebar {
    background-color: #1a1a1a;
}
</style>
""", unsafe_allow_html=True)

st.title("🔱 Divine Astrology Consultation Portal 🔱")
st.markdown("### Blessings & Guidance Awaits You ✨")

UPI_ID = "rajkumarpalanivel80@okaxis"

# ---------------- LOGOUT ----------------
if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# ---------------- AUTH ----------------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    # REGISTER
    if menu == "Register":
        st.subheader("Create Devotee Account")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                cursor.execute("INSERT INTO users VALUES (NULL,?,?,?,?)",
                               (u, hash_password(p), "user", 0))
                conn.commit()
                st.success("Account created successfully 🙏")
            except:
                st.error("Username already exists")

    # LOGIN
    if menu == "Login":
        st.subheader("Login")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (u, hash_password(p)))
            user = cursor.fetchone()

            if user:
                st.session_state.user = user[1]
                st.session_state.role = user[3]
                st.success("Welcome 🙏")
                st.rerun()
            else:
                st.error("Invalid credentials")

# ---------------- USER DASHBOARD ----------------
if st.session_state.role == "user":

    st.sidebar.success(f"Welcome {st.session_state.user}")

    option = st.sidebar.selectbox("Devotee Panel", [
        "Book Slot",
        "My Bookings"
    ])

    slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]

    # BOOK SLOT
    if option == "Book Slot":

        st.subheader("Available Divine Slots")

        cursor.execute("SELECT booking_count FROM users WHERE username=?",
                       (st.session_state.user,))
        booking_count = cursor.fetchone()[0]

        amount = 501 if booking_count == 0 else 301

        st.info(f"Consultation Fee: ₹{amount}")

        for slot in slots:
            cursor.execute("SELECT * FROM bookings WHERE slot=?", (slot,))
            booked = cursor.fetchone()

            if booked:
                st.error(f"{slot} - Booked ❌")
            else:
                if st.button(f"Book {slot}"):

                    upi_link = f"upi://pay?pa={UPI_ID}&pn=AstrologyConsultation&am={amount}&cu=INR"

                    qr = qrcode.make(upi_link)
                    buf = BytesIO()
                    qr.save(buf)
                    buf.seek(0)

                    st.image(buf, caption=f"Scan to Pay ₹{amount}")

                    if st.button("Confirm Payment"):
                        cursor.execute("""
                        INSERT INTO bookings VALUES(NULL,?,?,?,?,?)
                        """, (
                            st.session_state.user,
                            slot,
                            amount,
                            "Pending Approval",
                            str(datetime.now())
                        ))

                        cursor.execute("""
                        UPDATE users SET booking_count = booking_count + 1
                        WHERE username=?
                        """, (st.session_state.user,))

                        conn.commit()

                        st.success("Booking Request Sent 🙏 Await Approval")
                        st.rerun()

    # MY BOOKINGS
    if option == "My Bookings":

        st.subheader("Your Consultations")

        cursor.execute("SELECT * FROM bookings WHERE username=?",
                       (st.session_state.user,))
        data = cursor.fetchall()

        if not data:
            st.info("No bookings yet")

        for row in data:
            st.write(f"🕒 Slot: {row[2]}")
            st.write(f"💰 Amount: ₹{row[3]}")
            st.write(f"📌 Status: {row[4]}")
            st.write("---")

# ---------------- ADMIN DASHBOARD ----------------
if st.session_state.role == "admin":

    st.sidebar.success("Admin Panel 🔱")

    option = st.sidebar.selectbox("Admin Controls", [
        "Approve Bookings",
        "View Payments",
        "Upcoming Meetings"
    ])

    # APPROVE BOOKINGS
    if option == "Approve Bookings":

        st.subheader("Pending Approval")

        cursor.execute("SELECT * FROM bookings WHERE status='Pending Approval'")
        data = cursor.fetchall()

        if not data:
            st.info("No pending bookings")

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]} | ₹{row[3]}")
            if st.button(f"Approve {row[0]}"):
                cursor.execute("UPDATE bookings SET status='Approved' WHERE id=?",
                               (row[0],))
                conn.commit()
                st.success("Approved ✅")
                st.rerun()

    # VIEW PAYMENTS
    if option == "View Payments":

        st.subheader("Payments Received")

        cursor.execute("SELECT * FROM bookings")
        data = cursor.fetchall()

        total = sum([row[3] for row in data])
        st.success(f"Total Revenue: ₹{total}")

        for row in data:
            st.write(f"{row[1]} | {row[2]} | ₹{row[3]}")

    # UPCOMING MEETINGS
    if option == "Upcoming Meetings":

        st.subheader("Approved Consultations")

        cursor.execute("SELECT * FROM bookings WHERE status='Approved'")
        data = cursor.fetchall()

        if not data:
            st.info("No approved meetings")

        for row in data:
            st.write(f"{row[1]} - {row[2]} - ₹{row[3]}")admin_password = hash_password("admin123")

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                   ("admin", admin_password, "admin"))
    conn.commit()

# ---------- SESSION ----------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ---------- UI ----------
st.set_page_config(page_title="Astrology Client System", layout="centered")
st.title("🔮 Astrology Client Management System")
st.markdown("Developed by Pranav Naidu")

# ---------- LOGOUT ----------
if st.session_state.user:
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# ---------- AUTH MENU ----------
if not st.session_state.user:
    menu = st.sidebar.selectbox("Menu", ["Login", "Register"])

    # REGISTER
    if menu == "Register":
        st.subheader("Create User Account")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                cursor.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                               (u, hash_password(p), "user"))
                conn.commit()
                st.success("Account created successfully")
            except:
                st.error("Username already exists")

    # LOGIN
    if menu == "Login":
        st.subheader("Login")

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (u, hash_password(p)))
            user = cursor.fetchone()

            if user:
                st.session_state.user = user[1]
                st.session_state.role = user[3]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

# ---------- USER DASHBOARD ----------
if st.session_state.role == "user":

    st.sidebar.success(f"Logged in as: {st.session_state.user}")

    option = st.sidebar.selectbox("User Panel", [
        "Book Slot",
        "My Bookings"
    ])

    slots = ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM"]

    # BOOK SLOT
    if option == "Book Slot":
        st.subheader("Available Slots")

        for slot in slots:
            cursor.execute("SELECT * FROM bookings WHERE slot=?", (slot,))
            booked = cursor.fetchone()

            if booked:
                st.error(f"{slot} - Booked ❌")
            else:
                if st.button(f"Book {slot}"):
                    cursor.execute("""
                    INSERT INTO bookings VALUES(NULL,?,?,?,?,?)
                    """, (
                        st.session_state.user,
                        slot,
                        "Pending Approval",
                        "Paid",
                        str(datetime.now())
                    ))
                    conn.commit()
                    st.success("Booking request sent")
                    st.rerun()

    # MY BOOKINGS
    if option == "My Bookings":
        st.subheader("My Bookings")

        cursor.execute("SELECT * FROM bookings WHERE username=?",
                       (st.session_state.user,))
        data = cursor.fetchall()

        if not data:
            st.info("No bookings yet")

        for row in data:
            st.write(f"Slot: {row[2]}")
            st.write(f"Status: {row[3]}")
            st.write(f"Payment: {row[4]}")
            st.write("---")

# ---------- ADMIN DASHBOARD ----------
if st.session_state.role == "admin":

    st.sidebar.success("Admin Panel")

    option = st.sidebar.selectbox("Admin Controls", [
        "Approve Bookings",
        "View Payments",
        "Upcoming Meetings"
    ])

    # APPROVE BOOKINGS
    if option == "Approve Bookings":
        st.subheader("Pending Bookings")

        cursor.execute("SELECT * FROM bookings WHERE status='Pending Approval'")
        data = cursor.fetchall()

        if not data:
            st.info("No pending bookings")

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]}")
            if st.button(f"Approve {row[0]}"):
                cursor.execute("UPDATE bookings SET status='Approved' WHERE id=?",
                               (row[0],))
                conn.commit()
                st.success("Booking Approved")
                st.rerun()

    # VIEW PAYMENTS
    if option == "View Payments":
        st.subheader("Payments Received")

        cursor.execute("SELECT * FROM bookings WHERE payment='Paid'")
        data = cursor.fetchall()

        if not data:
            st.info("No payments yet")

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]}")

    # UPCOMING MEETINGS
    if option == "Upcoming Meetings":
        st.subheader("Approved Meetings")

        cursor.execute("SELECT * FROM bookings WHERE status='Approved'")
        data = cursor.fetchall()

        if not data:
            st.info("No approved meetings")

        for row in data:
            st.write(f"User: {row[1]} | Slot: {row[2]}")


