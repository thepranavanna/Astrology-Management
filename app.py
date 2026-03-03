import streamlit as st
import sqlite3
import hashlib
import qrcode
from io import BytesIO

# ---------------- DATABASE ----------------
conn = sqlite3.connect("astrology.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    slot TEXT,
    amount INTEGER,
    dob TEXT,
    birth_time TEXT,
    birth_place TEXT,
    contact TEXT,
    transaction_id TEXT,
    message TEXT,
    status TEXT
)
""")

conn.commit()

# ---------------- FUNCTIONS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_qr(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "booking_data" not in st.session_state:
    st.session_state.booking_data = None

st.title("🔮 Astrology Kundli Booking System")

# ---------------- MENU ----------------
if st.session_state.user == "admin":
    menu = ["Admin Panel", "Logout"]
elif st.session_state.user:
    menu = ["Book Slot", "My Bookings", "Logout"]
else:
    menu = ["Login", "Create Account"]

choice = st.sidebar.selectbox("Menu", menu)

# ---------------- CREATE ACCOUNT ----------------
if choice == "Create Account":
    st.subheader("Create Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, hash_password(password)))
            conn.commit()
            st.success("Account created successfully!")
        except:
            st.error("Username already exists!")

# ---------------- LOGIN ----------------
elif choice == "Login":
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.user = "admin"
            st.success("Admin Logged In")
        else:
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (username, hash_password(password)))
            user = cursor.fetchone()
            if user:
                st.session_state.user = username
                st.success("Login Successful")
            else:
                st.error("Invalid Credentials")

# ---------------- BOOK SLOT ----------------
elif choice == "Book Slot":
    st.subheader("Book Kundli Appointment")

    slot = st.selectbox("Select Slot", ["10 AM", "1 PM", "4 PM", "7 PM"])
    amount = 500
    st.write("Amount to Pay: ₹500")

    st.subheader("Birth Details")
    dob = st.date_input("Date of Birth")
    birth_time = st.time_input("Accurate Time of Birth")
    birth_place = st.text_input("Place of Birth")

    if st.button("Generate QR to Pay"):
        if birth_place.strip() == "":
            st.error("Please enter place of birth.")
        else:
            upi_id = "rajkumarpalanivel80@okaxis"
            payment_link = f"upi://pay?pa={upi_id}&pn=Astrology&am={amount}&cu=INR"
            qr_image = generate_qr(payment_link)
            st.image(qr_image)

            st.session_state.booking_data = {
                "username": st.session_state.user,
                "slot": slot,
                "amount": amount,
                "dob": str(dob),
                "birth_time": str(birth_time),
                "birth_place": birth_place
            }

    if st.session_state.booking_data:
        st.subheader("After Payment Details")

        contact = st.text_input("Contact Number")
        transaction_id = st.text_input("Transaction ID")
        message = st.text_area("Message (Optional)")

        if st.button("Submit Booking"):
            if contact == "" or transaction_id == "":
                st.error("Contact and Transaction ID are required!")
            else:
                cursor.execute("""
                INSERT INTO bookings
                (username, slot, amount, dob, birth_time, birth_place,
                 contact, transaction_id, message, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    st.session_state.booking_data["username"],
                    st.session_state.booking_data["slot"],
                    st.session_state.booking_data["amount"],
                    st.session_state.booking_data["dob"],
                    st.session_state.booking_data["birth_time"],
                    st.session_state.booking_data["birth_place"],
                    contact,
                    transaction_id,
                    message,
                    "Pending"
                ))
                conn.commit()
                st.success("Booking submitted! Admin will verify payment.")
                st.session_state.booking_data = None

# ---------------- MY BOOKINGS ----------------
elif choice == "My Bookings":
    st.subheader("My Bookings")

    cursor.execute("""
    SELECT slot, amount, status
    FROM bookings WHERE username=?
    """, (st.session_state.user,))
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            st.write(f"Slot: {row[0]} | ₹{row[1]} | Status: {row[2]}")
    else:
        st.info("No bookings yet.")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":

    admin_menu = st.sidebar.radio(
        "Admin Options",
        ["View Clients", "View Appointments", "View Payments", "Reschedule Appointment"]
    )

    # VIEW CLIENTS
    if admin_menu == "View Clients":
        st.subheader("All Clients")
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
        for user in users:
            if user[1] != "admin":
                st.write(f"ID: {user[0]} | Username: {user[1]}")

    # VIEW APPOINTMENTS
    elif admin_menu == "View Appointments":
        st.subheader("All Appointments")
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()

        for row in bookings:
            st.write("-----------")
            st.write(f"Booking ID: {row[0]}")
            st.write(f"User: {row[1]}")
            st.write(f"Slot: {row[2]}")
            st.write(f"DOB: {row[4]}")
            st.write(f"Birth Time: {row[5]}")
            st.write(f"Birth Place: {row[6]}")
            st.write(f"Contact: {row[7]}")
            st.write(f"Status: {row[10]}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Approve {row[0]}"):
                    cursor.execute("UPDATE bookings SET status='Approved' WHERE id=?",
                                   (row[0],))
                    conn.commit()
                    st.rerun()

            with col2:
                if st.button(f"Reject {row[0]}"):
                    cursor.execute("UPDATE bookings SET status='Rejected' WHERE id=?",
                                   (row[0],))
                    conn.commit()
                    st.rerun()

    # VIEW PAYMENTS
    elif admin_menu == "View Payments":
        st.subheader("Payment Details")
        cursor.execute("SELECT id, username, amount, transaction_id, status FROM bookings")
        payments = cursor.fetchall()

        for row in payments:
            st.write("-----------")
            st.write(f"Booking ID: {row[0]}")
            st.write(f"User: {row[1]}")
            st.write(f"Amount: ₹{row[2]}")
            st.write(f"Transaction ID: {row[3]}")
            st.write(f"Status: {row[4]}")

    # RESCHEDULE
    elif admin_menu == "Reschedule Appointment":
        st.subheader("Reschedule Approved Appointment")

        cursor.execute("SELECT id, slot FROM bookings WHERE status='Approved'")
        approved = cursor.fetchall()

        if approved:
            ids = [str(row[0]) for row in approved]
            selected_id = st.selectbox("Select Booking ID", ids)

            new_slot = st.selectbox("New Slot",
                                    ["10 AM", "1 PM", "4 PM", "7 PM"])

            if st.button("Update Slot"):
                cursor.execute("UPDATE bookings SET slot=? WHERE id=?",
                               (new_slot, selected_id))
                conn.commit()
                st.success("Appointment Rescheduled")
                st.rerun()
        else:
            st.info("No approved bookings available.")

# ---------------- LOGOUT ----------------
elif choice == "Logout":
    st.session_state.user = None
    st.success("Logged out successfully.")
