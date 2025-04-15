import streamlit as st
import hashlib
import json
import time
from cryptography.fernet import Fernet
import base64

# Initialize session state variables if they don't exist
if 'failed_attempts' not in st.session_state:
    st.session_state.failed_attempts = 0
if 'stored_data' not in st.session_state:
    st.session_state.stored_data = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'last_attempt_time' not in st.session_state:
    st.session_state.last_attempt_time = 0

# Function to hash passkey
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

# Function to generate encryption key from passkey
def generate_key_from_passkey(passkey):
    hashed = hashlib.sha3_256(passkey.encode()).digest()
    return base64.urlsafe_b64encode(hashed[:32])

# Function to encrypt data
def encrypt_data(text, passkey):
    key = generate_key_from_passkey(passkey)
    cipher = Fernet(key)
    return cipher.encrypt(text.encode()).decode()

# Function to decrypt data
def decrypt_data(encrypted_text, passkey, data_id):
    try:
        hashed_passkey = hash_passkey(passkey)
        if data_id in st.session_state.stored_data and st.session_state.stored_data[data_id]['hashed_passkey'] == hashed_passkey:
            key = generate_key_from_passkey(passkey)
            cipher = Fernet(key)
            decrypted = cipher.decrypt(encrypted_text.encode()).decode()
            st.session_state.failed_attempts = 0
            return decrypted
        else:
            st.session_state.failed_attempts += 1
            st.session_state.last_attempt_time = time.time()
            return None
    except Exception as e:
        st.session_state.failed_attempts += 1
        st.session_state.last_attempt_time = time.time()
        return None

# Function to generate a unique ID for data
def generate_data_id():
    import uuid
    return str(uuid.uuid4())

# Reset failed attempts
def reset_failed_attempts():
    st.session_state.failed_attempts = 0

# Change page function
def change_page(page):
    st.session_state.current_page = page

# Streamlit UI
st.title("🔐 Secure Data Encryption System")
st.sidebar.title("Navigation")
menu = ["Home", "Store Data", "Retrieve Data", "Login"]
choice = st.sidebar.selectbox("Navigation", menu, index=menu.index(st.session_state.current_page))

# Update current page
st.session_state.current_page = choice

# Check if too many failed attempts
if st.session_state.failed_attempts >= 3:
    st.session_state.current_page = "Login"
    st.warning("⚠ Too many failed attempts. Please login again.")

# Display pages
if st.session_state.current_page == "Home":
    st.header("💒 Welcome to the Secure Data System")
    st.write("This application allows you to **securely store and retrieve data** using unique passkeys.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Store New Data", use_container_width=True):
            change_page("Store Data")
    with col2:
        if st.button("Retrieve Data", use_container_width=True):
            change_page("Retrieve Data")

    st.info(f"🔒 You have stored {len(st.session_state.stored_data)} data entries.")

elif st.session_state.current_page == "Store Data":
    st.subheader("📂 Store Data Securely")
    user_data = st.text_area("Enter the data you want to store:")
    passkey = st.text_input("Enter a passkey to encrypt your data:", type="password")
    confirm_passkey = st.text_input("Confirm your passkey:", type="password")

    if st.button("Encrypt & Save"):
        if user_data and passkey and confirm_passkey:
            if passkey != confirm_passkey:
                st.error("❌ Passkeys do not match!")
            else:
                data_id = generate_data_id()
                hashed_passkey = hash_passkey(passkey)
                encrypted_text = encrypt_data(user_data, passkey)

                st.session_state.stored_data[data_id] = {
                    "encrypted_text": encrypted_text,
                    "hashed_passkey": hashed_passkey,  # ✅ Corrected key name
                }

                st.success("✅ Data stored successfully!")
                st.code(data_id, language="text")
                st.info("🔑 Keep this ID safe for data retrieval.")
        else:
            st.error("❌ Please fill in all fields.")

elif st.session_state.current_page == "Retrieve Data":
    st.subheader("🔍 Retrieve Your Data")

    attempts_remaining = 3 - st.session_state.failed_attempts
    st.info(f"🔑 Attempts remaining: {attempts_remaining}")

    data_id = st.text_input("Enter the data ID to retrieve:")
    passkey = st.text_input("Enter your passkey:", type="password")

    if st.button("Decrypt"):
        if data_id and passkey:
            if data_id in st.session_state.stored_data:
                encrypted_text = st.session_state.stored_data[data_id]["encrypted_text"]
                decrypted_text = decrypt_data(encrypted_text, passkey, data_id)
                if decrypted_text:
                    st.success("✅ Data decrypted successfully!")
                    st.markdown("### Your Data:")
                    st.code(decrypted_text, language="text")
                else:
                    st.error(f"❌ Incorrect passkey or data ID. Attempts remaining: {3 - st.session_state.failed_attempts}")
            else:
                st.error("❌ Invalid data ID.")

            if st.session_state.failed_attempts >= 3:
                st.warning("⚠ Too many failed attempts. Please login again.")
                st.session_state.current_page = "Login"
                st.rerun()
        else:
            st.error("❌ Please fill in all fields.")

elif st.session_state.current_page == "Login":
    st.subheader("🔑 Reauthorization Required")

    if time.time() - st.session_state.last_attempt_time < 10 and st.session_state.failed_attempts >= 3:
        remaining_time = int(10 - (time.time() - st.session_state.last_attempt_time))
        st.warning(f"🕕 Too many failed attempts. Please wait {remaining_time} seconds before trying again.")
    else:
        login_pass = st.text_input("Enter password to login:", type="password")

        if st.button("Login"):
            if login_pass == "masterkey123":
                reset_failed_attempts()
                st.success("✅ Authorization successful!")
                st.session_state.current_page = "Home"
                st.rerun()
            else:
                st.error("❌ Incorrect password.")

# Footer
st.markdown("---")
st.markdown("### Developed by Areeba Saleem")
st.markdown("Copyright © 2023. All rights reserved.")
