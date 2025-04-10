import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# === Secret API Keys ===
GEMINI_API_KEY = "AIzaSyAbXv94hwzhbrxhBYq-zS58LkhKZQ6cjMg"
LLAMA_URL = "https://api.llmapi.com/"

# === Files for persistence ===
USER_FILE = "users.csv"
POST_FILE = "posts.csv"
IMG_DIR = "uploaded_images"

# === Setup ===
os.makedirs(IMG_DIR, exist_ok=True)
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)
if not os.path.exists(POST_FILE):
    pd.DataFrame(columns=["username", "content", "timestamp", "likes", "comments", "image_path"]).to_csv(POST_FILE, index=False)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# === Internal Gemini Call ===
def _ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data)
    return response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else ""

# === Internal LLaMA Call ===
def _ask_llama(prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "max_tokens": 300,
        "temperature": 0.7
    }
    response = requests.post(LLAMA_URL, headers=headers, json=data)
    return response.json().get("response", "").strip()

# === Merge AI Responses ===
def merge_as_firebox(response1, response2):
    prompt = f"""
You are Firebox, a smart assistant. You got two draft answers.

A: {response1}
B: {response2}

Merge them into one, clearly and helpfully. Do not mention any tools used. Just respond as Firebox.
"""
    return _ask_gemini(prompt)

# === Register ===
def register():
    st.subheader("🧑 Register")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        df = pd.read_csv(USER_FILE)
        if email in df.email.values:
            st.warning("Email already registered.")
        elif username in df.username.values:
            st.warning("Username taken.")
        else:
            new_user = pd.DataFrame([[email, username, password]], columns=df.columns)
            df = pd.concat([df, new_user], ignore_index=True)
            df.to_csv(USER_FILE, index=False)
            st.success("🎉 Registered!")

# === Login ===
def login():
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        df = pd.read_csv(USER_FILE)
        user = df[(df.email == email) & (df.password == password)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = user.iloc[0]["username"]
            st.success(f"Welcome, {st.session_state.username}!")
        else:
            st.error("Invalid credentials.")

# === Firebox Chat ===
def firebox_chat():
    st.subheader("🤖 Ask Firebox AI")
    user_prompt = st.text_input("Ask something...")
    if st.button("Answer"):
        with st.spinner("Firebox is thinking..."):
            g = _ask_gemini(user_prompt)
            l = _ask_llama(user_prompt)
            answer = merge_as_firebox(g, l)
            st.success(answer)

# === Social Feed ===
def social_feed():
    st.title("🔥 Firebox Social")
    st.write(f"Logged in as **{st.session_state.username}**")

    st.subheader("📢 New Post")
    text = st.text_area("What's on your mind?")
    image = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if st.button("Post"):
        if text.strip() != "":
            image_path = ""
            if image:
                image_path = os.path.join(IMG_DIR, f"{datetime.now().timestamp()}_{image.name}")
                with open(image_path, "wb") as f:
                    f.write(image.getbuffer())

            posts = pd.read_csv(POST_FILE)
            new_post = {
                "username": st.session_state.username,
                "content": text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "likes": 0,
                "comments": "",
                "image_path": image_path
            }
            posts = pd.concat([posts, pd.DataFrame([new_post])], ignore_index=True)
            posts.to_csv(POST_FILE, index=False)
            st.success("Posted!")
            st.experimental_rerun()

    st.markdown("---")
    posts = pd.read_csv(POST_FILE)
    if posts.empty:
        st.info("No posts yet.")
    else:
        posts = posts.sort_values(by="timestamp", ascending=False)
        for idx, row in posts.iterrows():
            st.markdown(f"**{row['username']}** @ {row['timestamp']}")
            st.markdown(row['content'])
            if isinstance(row['image_path'], str) and os.path.exists(row['image_path']):
                st.image(row['image_path'], use_column_width=True)
            st.markdown(f"❤️ {row['likes']} likes")

            if st.button(f"Like {idx}"):
                posts.at[idx, 'likes'] += 1
                posts.to_csv(POST_FILE, index=False)
                st.experimental_rerun()

            comment = st.text_input(f"Comment {idx}", key=f"comment_{idx}")
            if st.button(f"Comment {idx}"):
                if comment.strip():
                    row_comments = posts.at[idx, 'comments']
                    updated = f"{row_comments} [{st.session_state.username}]: {comment} |"
                    posts.at[idx, 'comments'] = updated
                    posts.to_csv(POST_FILE, index=False)
                    st.experimental_rerun()

            if row['comments']:
                st.markdown("💬 Comments:")
                for c in row['comments'].split("|"):
                    if c.strip():
                        st.markdown(f"- {c.strip()}")

            st.markdown("---")

# === Floating Firebox Icon ===
def firebox_icon():
    st.markdown("""
    <style>
        .floating-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #ff4b4b;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 28px;
            color: white;
            text-align: center;
            line-height: 50px;
            z-index: 9999;
        }
    </style>
    <a href="#firebox" class="floating-btn">🔥</a>
    """, unsafe_allow_html=True)

# === Main App ===
def main():
    firebox_icon()
    menu = st.sidebar.radio("Menu", ["Home", "Register", "Login", "Logout"])
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
        firebox_chat()
        social_feed()
    else:
        st.title("🔥 Welcome to Firebox")
        st.info("Please register or login to continue.")

if __name__ == "__main__":
    main()
