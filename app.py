import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# === API KEYS ===
GEMINI_API_KEY = "AIzaSyAbXv94hwzhbrxhBYq-zS58LkhKZQ6cjMg"  # 🔑 Replace with your key
LLAMA_API_URL = "https://api.llmapi.com/"  # 🔗 No API key required in this version

# === File Paths ===
USER_FILE = "users.csv"
POST_FILE = "posts.csv"

# === File Initialization ===
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)

if not os.path.exists(POST_FILE):
    pd.DataFrame(columns=["username", "content", "timestamp", "likes", "comments"]).to_csv(POST_FILE, index=False)

# === Session State ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# === Firebox AI: Gemini ===
def ask_firebox_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    response = requests.post(url, json=payload)
    try:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "❗ Error from Firebox Gemini Engine."

# === Firebox AI: LLaMA ===
def ask_firebox_llama(prompt):
    payload = {
        "prompt": prompt,
        "model": "llama2-13b-chat",
        "temperature": 0.7,
        "max_tokens": 300
    }
    response = requests.post(LLAMA_API_URL, json=payload)
    try:
        return response.json().get("response", "❗ No reply from Firebox LLaMA Engine.")
    except:
        return "❗ Error from Firebox LLaMA Engine."

# === Firebox AI Chatbox ===
def firebox_ai():
    st.title("🔥 Firebox AI Assistant")
    model = st.selectbox("Choose Firebox AI Engine", ["Gemini", "LLaMA"])
    prompt = st.text_area("💬 Ask Firebox anything...")

    if st.button("Get Answer"):
        with st.spinner("Firebox is thinking..."):
            if model == "Gemini":
                answer = ask_firebox_gemini(prompt)
            else:
                answer = ask_firebox_llama(prompt)
        st.markdown("### 🧠 Firebox says:")
        st.success(answer)

# === Register ===
def register():
    st.subheader("🔐 Create a Firebox Account")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Sign Up"):
        df = pd.read_csv(USER_FILE)
        if email in df['email'].values:
            st.warning("Email already registered.")
        elif username in df['username'].values:
            st.warning("Username already taken.")
        else:
            new_user = pd.DataFrame([[email, username, password]], columns=df.columns)
            df = pd.concat([df, new_user], ignore_index=True)
            df.to_csv(USER_FILE, index=False)
            st.success("Registration successful! 🎉")

# === Login ===
def login():
    st.subheader("🔓 Login to Firebox")
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

# === Social Feed ===
def social_feed():
    st.title("🔥 Firebox Social Feed")
    st.write(f"👤 Logged in as: **{st.session_state.username}**")

    post = st.text_area("📝 What's on your mind?")
    if st.button("Post"):
        if post.strip():
            post_data = pd.read_csv(POST_FILE)
            new_post = {
                "username": st.session_state.username,
                "content": post,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "likes": 0,
                "comments": ""
            }
            post_data = pd.concat([post_data, pd.DataFrame([new_post])], ignore_index=True)
            post_data.to_csv(POST_FILE, index=False)
            st.success("✅ Posted!")

    st.markdown("---")
    post_data = pd.read_csv(POST_FILE)
    if post_data.empty:
        st.info("No posts yet. Be the first!")
    else:
        post_data = post_data.sort_values(by="timestamp", ascending=False)
        for idx, row in post_data.iterrows():
            st.markdown(f"**{row['username']}** at {row['timestamp']}")
            st.markdown(f"{row['content']}")
            st.markdown(f"❤️ {row['likes']} likes")
            
            if st.button(f"Like {idx}"):
                post_data.at[idx, 'likes'] += 1
                post_data.to_csv(POST_FILE, index=False)
                st.experimental_rerun()

            comment = st.text_input(f"💬 Comment on post {idx}", key=f"comment_{idx}")
            if st.button(f"Add Comment {idx}"):
                if comment.strip():
                    current_comments = post_data.at[idx, 'comments']
                    updated = f"{current_comments} [{st.session_state.username}]: {comment} |"
                    post_data.at[idx, 'comments'] = updated
                    post_data.to_csv(POST_FILE, index=False)
                    st.experimental_rerun()

            if row['comments']:
                st.markdown("*Comments:*")
                for c in row['comments'].split("|"):
                    if c.strip():
                        st.markdown(f"- {c.strip()}")
            st.markdown("---")

# === Main App ===
def main():
    st.set_page_config(page_title="🔥 Firebox", layout="centered")
    st.sidebar.title("🚀 Firebox Menu")
    menu = st.sidebar.selectbox("Navigate", ["Home", "Register", "Login", "Logout", "Firebox AI"])

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
        st.success("Logged out.")
    elif menu == "Firebox AI":
        firebox_ai()

    if st.session_state.logged_in and menu == "Home":
        social_feed()

if __name__ == "__main__":
    main()
