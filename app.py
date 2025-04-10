import streamlit as st
import pandas as pd
import os

# Load or create user database
if not os.path.exists("users.csv"):
    df = pd.DataFrame(columns=["email", "username", "password"])
    df.to_csv("users.csv", index=False)

# UI
st.title("Firebox Social – Register")
email = st.text_input("Enter your email")
username = st.text_input("Choose a username")
password = st.text_input("Set a password", type="password")

if st.button("Register"):
    df = pd.read_csv("users.csv")
    
    if email in df['email'].values:
        st.warning("Email already registered.")
    elif username in df['username'].values:
        st.warning("Username already taken.")
    else:
        new_user = pd.DataFrame([[email, username, password]], columns=df.columns)
        df = pd.concat([df, new_user], ignore_index=True)
        df.to_csv("users.csv", index=False)
        st.success("Registration successful 🎉")

