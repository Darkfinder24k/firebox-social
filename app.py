# === 🔥 Firebox Full Social AI App ===
import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime

# === API Keys ===
GEMINI_API_KEY = "AIzaSyAbXv94hwzhbrxhBYq-zS58LkhKZQ6cjMg"

# === File Paths ===
USER_FILE = "users.csv"
POST_FILE = "posts.csv"

# === Create Files If Missing ===
os.makedirs("uploads", exist_ok=True)
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)
if not os.path.exists(POST_FILE):
    pd.DataFrame(columns=["username", "content", "timestamp", "likes", "comments", "image_path"]).to_csv(POST_FILE, index=False)

# === Session State ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# === Ask Gemini ===
def _ask_gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(f"{url}?key={GEMINI_API_KEY}", headers=headers, json=data)
    return response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else ""

# === Ask LLaMA via llmapi.com ===
def _ask_llama(prompt):
    url = "https://api.llmapi.com/"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "llama2",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['response'].strip() if response.status_code == 200 else ""

# === Merge Responses ===
def merge_as_firebox(resp1, resp2):
    merge_prompt = f"""
You are Firebox AI. You received two drafts of a response.

Response A: {resp1}
Response B: {resp2}

Merge them into a clear, intelligent, natural-sounding reply. Do not mention Gemini, LLaMA, or Google. Just respond as Firebox.
"""
    return _ask_gemini(merge_prompt)

# === Register ===
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
            st.success("Registered! Please log in.")

# === Login ===
def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Log In"):
        df = pd.read_csv(USER_FILE)
        user = df[(df['email'] == email) & (df['password'] == password)]
        if not user.empty:
            st.session_state.logged_in = True
            st.session_state.username = user.iloc[0]['username']
            st.success(f"Welcome {st.session_state.username}!")
        else:
            st.error("Invalid login credentials.")

# === Firebox AI Chat ===
def firebox_chat():
    st.subheader("🤖 Ask Firebox AI")
    user_q = st.text_area("Ask something...")
    if st.button("Get Firebox Answer") and user_q.strip():
        with st.spinner("Thinking..."):
            gem = _ask_gemini(user_q)
            lla = _ask_llama(user_q)
            answer = merge_as_firebox(gem, lla)
            st.markdown("### 🔥 Firebox says:")
            st.success(answer)

# === Feed ===
def social_feed():
    st.title("🔥 Firebox Social")
    st.write(f"Logged in as **{st.session_state.username}**")

    # Post something
    st.subheader("New Post")
    content = st.text_area("What's on your mind?")
    image = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if st.button("Post"):
        image_path = ""
        if image:
            image_path = os.path.join("uploads", f"{datetime.now().timestamp()}_{image.name}")
            with open(image_path, "wb") as f:
                f.write(image.read())

        df = pd.read_csv(POST_FILE)
        new_post = {
            "username": st.session_state.username,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "likes": 0,
            "comments": "",
            "image_path": image_path
        }
        df = pd.concat([df, pd.DataFrame([new_post])], ignore_index=True)
        df.to_csv(POST_FILE, index=False)
        st.success("Posted!")
        st.experimental_rerun()

    st.markdown("---")

    df = pd.read_csv(POST_FILE)
    if df.empty:
        st.info("No posts yet.")
    else:
        df = df.sort_values(by="timestamp", ascending=False)
        for idx, row in df.iterrows():
            st.markdown(f"**{row['username']}** posted at {row['timestamp']}")
            if row['image_path']:
                st.image(row['image_path'], width=300)
            st.markdown(row['content'])
            st.markdown(f"❤️ {row['likes']} likes")

            if st.button(f"Like {idx}"):
                df.at[idx, 'likes'] += 1
                df.to_csv(POST_FILE, index=False)
                st.experimental_rerun()

            # Comment section
            comment = st.text_input(f"Comment {idx}", key=f"cmt_{idx}")
            if st.button(f"Add Comment {idx}"):
                if comment.strip():
                    current = df.at[idx, 'comments']
                    updated = current + f"[{st.session_state.username}]: {comment} |"
                    df.at[idx, 'comments'] = updated
                    df.to_csv(POST_FILE, index=False)
                    st.experimental_rerun()

            if row['comments']:
                st.markdown("*Comments:*")
                for c in row['comments'].split("|"):
                    if c.strip():
                        st.markdown(f"- {c.strip()}")
            st.markdown("---")

# === Main App ===
def main():
    st.set_page_config(page_title="🔥 Firebox AI + Social", layout="wide")
    menu = st.sidebar.selectbox("Menu", ["Login", "Register", "Firebox AI", "Logout"])

    if menu == "Register":
        register()
    elif menu == "Login":
        if not st.session_state.logged_in:
            login()
        else:
            st.success(f"Logged in as {st.session_state.username}")
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out")

    if st.session_state.logged_in:
        firebox_chat()
        social_feed()

if __name__ == "__main__":
    main()
