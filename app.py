# firebox_social_ai_app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import base64
import requests

# === API KEYS ===
GEMINI_API_KEY = "AIzaSyAbXv94hwzhbrxhBYq-zS58LkhKZQ6cjMg"

# === FILE PATHS ===
USER_FILE = "users.csv"
POST_FILE = "posts.csv"
IMAGE_DIR = "post_images"

# === INIT ===
os.makedirs(IMAGE_DIR, exist_ok=True)
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)
if not os.path.exists(POST_FILE):
    pd.DataFrame(columns=["username", "content", "timestamp", "likes", "comments", "image"]).to_csv(POST_FILE, index=False)

# === DARK MODE ===
st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .css-1v0mbdj, .stTextInput > div > div, .stTextArea, .stButton, .stMarkdown, .stFileUploader { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# === SESSION ===
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if 'show_ai' not in st.session_state:
    st.session_state.show_ai = False

# === Gemini API (internalized) ===
def _ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return "Error generating response."

# === Auth Pages ===
def register():
    st.subheader("Register")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        df = pd.read_csv(USER_FILE)
        if email in df['email'].values:
            st.warning("Email already registered.")
        elif username in df['username'].values:
            st.warning("Username taken.")
        else:
            new_user = pd.DataFrame([[email, username, password]], columns=df.columns)
            df = pd.concat([df, new_user], ignore_index=True)
            df.to_csv(USER_FILE, index=False)
            st.success("Registration successful 🎉")

def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Log In"):
        df = pd.read_csv(USER_FILE)
        user = df[(df['email'] == email) & (df['password'] == password)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = user.iloc[0]["username"]
            st.success(f"Welcome, {st.session_state.username}!")
        else:
            st.error("Invalid credentials.")

# === Firebox Icon Trigger ===
def floating_firebox():
    st.markdown("""
    <style>
    .firebox-btn {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #ff5722;
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        z-index: 9999;
    }
    </style>
    <button class="firebox-btn" onclick="window.location.href='#firebox'">🔥</button>
    """, unsafe_allow_html=True)

# === Social Feed ===
def social_feed():
    st.title("🔥 Firebox Social")
    st.write(f"Logged in as **{st.session_state.username}**")
    st.markdown("---")

    post_text = st.text_area("What's on your mind?")
    image_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg"])

    if st.button("Post"):
        post_data = pd.read_csv(POST_FILE)
        img_path = ""
        if image_file:
            img_name = f"{datetime.now().timestamp()}_{image_file.name}"
            img_path = os.path.join(IMAGE_DIR, img_name)
            with open(img_path, "wb") as f:
                f.write(image_file.getbuffer())

        new_post = {
            "username": st.session_state.username,
            "content": post_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "likes": 0,
            "comments": "",
            "image": img_path
        }
        post_data = pd.concat([post_data, pd.DataFrame([new_post])], ignore_index=True)
        post_data.to_csv(POST_FILE, index=False)
        st.success("Posted!")

    st.markdown("---")

    post_data = pd.read_csv(POST_FILE)
    post_data = post_data.sort_values(by="timestamp", ascending=False)

    for idx, row in post_data.iterrows():
        st.markdown(f"**{row['username']}** posted at {row['timestamp']}")
        st.markdown(f"{row['content']}")
        if pd.notna(row['image']) and os.path.exists(row['image']):
            st.image(row['image'], width=400)
        st.markdown(f"❤️ {row['likes']} likes")

        comment = st.text_input(f"Comment on post {idx}", key=f"comment_{idx}")
        if st.button(f"Add Comment {idx}"):
            if comment.strip():
                post_data = pd.read_csv(POST_FILE)
                current_comments = post_data.at[idx, 'comments']
                new_comments = f"{current_comments} [{st.session_state.username}]: {comment} |"
                post_data.at[idx, 'comments'] = new_comments
                post_data.to_csv(POST_FILE, index=False)

        if row['comments']:
            st.markdown("*Comments:*")
            for comment_text in str(row['comments']).split("|"):
                if comment_text.strip():
                    st.markdown(f"- {comment_text.strip()}")

        st.markdown("---")

# === Firebox Assistant ===
def firebox_ai():
    st.subheader("🤖 Ask Firebox AI")
    prompt = st.text_area("Ask something...")
    if st.button("Get Answer"):
        with st.spinner("Firebox is thinking..."):
            reply = _ask_gemini(prompt)
            st.success(reply)

# === Main ===
def main():
    floating_firebox()
    menu = st.sidebar.selectbox("Menu", ["Home", "Register", "Login", "Logout"])
    if menu == "Register":
        register()
    elif menu == "Login":
        if not st.session_state.logged_in:
            login()
        else:
            st.success(f"Already logged in as {st.session_state.username}")
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out successfully.")

    if st.session_state.logged_in:
        social_feed()
        st.markdown("<h3 id='firebox'></h3>", unsafe_allow_html=True)
        firebox_ai()

if __name__ == "__main__":
    main()
