import streamlit as st
import pandas as pd
import os
import time
import requests
from datetime import datetime

# ---------- File Setup ----------
POSTS_CSV = "posts.csv"
USERS_CSV = "users.csv"

if not os.path.exists(POSTS_CSV):
    df = pd.DataFrame(columns=['username', 'timestamp', 'text', 'image_path', 'likes', 'comments'])
    df.to_csv(POSTS_CSV, index=False)

if not os.path.exists(USERS_CSV):
    users_df = pd.DataFrame(columns=['email', 'username', 'password'])
    users_df.to_csv(USERS_CSV, index=False)

# ---------- User Auth ----------
def register_user():
    st.subheader("Register")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        users_df = pd.read_csv(USERS_CSV)
        if username in users_df['username'].values:
            st.error("Username already exists")
        else:
            new_user = pd.DataFrame([[email, username, password]], columns=['email', 'username', 'password'])
            new_user.to_csv(USERS_CSV, mode='a', header=False, index=False)
            st.success("Registered successfully. Please login.")

def login_user():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users_df = pd.read_csv(USERS_CSV)
        if ((users_df['username'] == username) & (users_df['password'] == password)).any():
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Logged in as {username}")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------- Post Upload ----------
def new_post():
    st.subheader("New Post")
    post_text = st.text_area("What's on your mind?")
    uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if st.button("Post"):
        image_path = ""
        if uploaded_file is not None:
            if not os.path.exists("images"):
                os.makedirs("images")
            image_path = os.path.join("images", f"{int(time.time())}_{uploaded_file.name}")
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        new_data = pd.DataFrame([[st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), post_text, image_path, 0, ""]],
                                columns=['username', 'timestamp', 'text', 'image_path', 'likes', 'comments'])
        new_data.to_csv(POSTS_CSV, mode='a', header=False, index=False)
        st.success("Posted!")
        st.rerun()

# ---------- Social Feed ----------
def social_feed():
    st.subheader("🔥 Firebox Social")

    try:
        df = pd.read_csv(POSTS_CSV)
        expected_cols = ['username', 'timestamp', 'text', 'image_path', 'likes', 'comments']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "" if col in ['text', 'image_path', 'comments'] else 0
    except Exception as e:
        st.error(f"Failed to load posts: {e}")
        return

    if 'liked_posts' not in st.session_state:
        st.session_state.liked_posts = set()

    for index, row in df[::-1].iterrows():
        try:
            username = row['username']
            timestamp = row['timestamp']
            post_text = row.get('text', '')
            image_path = row.get('image_path', '')
            likes = int(row.get('likes', 0))
            comments_raw = row.get('comments', '')

            st.markdown(f"**{username}** at {timestamp}")
            st.markdown(post_text if pd.notna(post_text) else "")

            if pd.notna(image_path) and os.path.exists(image_path):
                st.image(image_path, width=400)

            post_key = f"{username}_{timestamp}"
            if post_key not in st.session_state.liked_posts:
                if st.button("👍 Like", key=f"like_{index}"):
                    df.at[index, 'likes'] = likes + 1
                    st.session_state.liked_posts.add(post_key)
                    df.to_csv(POSTS_CSV, index=False)
                    st.rerun()
            else:
                st.markdown("✅ You already liked this post.")
            st.markdown(f"Likes: {int(df.at[index, 'likes'])}")

            # Comments section
            with st.expander("💬 Comments"):
                if pd.isna(comments_raw):
                    comments_raw = ""
                comments = comments_raw.split("|") if comments_raw else []

                for c in comments:
                    if c:
                        st.markdown(f"- {c}")

                new_comment = st.text_input("Add a comment", key=f"comment_{index}")
                if st.button("Comment", key=f"comment_btn_{index}"):
                    updated_comment = f"{st.session_state.username}: {new_comment}"
                    combined_comments = comments_raw + f"|{updated_comment}" if comments_raw else updated_comment
                    df.at[index, 'comments'] = combined_comments
                    df.to_csv(POSTS_CSV, index=False)
                    st.rerun()

        except Exception as e:
            st.error(f"Post error: {e}")

# ---------- Firebox AI ----------
def firebox_ai():
    st.subheader("🤖 Ask Firebox AI")
    prompt = st.text_input("Ask something...")
    if st.button("Ask"):
        st.write("Thinking...")

        # LLaMA
        try:
            llama_resp = requests.post("https://api.llmapi.com/", json={"prompt": prompt, "temperature": 0.7})
            llama_text = llama_resp.json().get("text", "")
        except:
            llama_text = "LLaMA failed."

        # Gemini
        try:
            gemini_api_key = "AIzaSyAbXv94hwzhbrxhBYq-zS58LkhKZQ6cjMg"
            gemini_resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={gemini_api_key}",
                json={"prompt": {"text": prompt}}
            )
            gemini_text = gemini_resp.json()['candidates'][0]['output']
        except:
            gemini_text = "Gemini failed."

        # Combine responses
        st.markdown("**Firebox Response:**")
        st.write(f"**LLaMA:** {llama_text}")
        st.write(f"**Gemini:** {gemini_text}")

# ---------- Main ----------
def main():
    st.set_page_config(page_title="Firebox Social", layout="centered")
    st.sidebar.title("🔥 Firebox")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        menu = st.sidebar.radio("Menu", ["Home", "New Post", "Ask Firebox AI", "Logout"])

        if menu == "Home":
            social_feed()
        elif menu == "New Post":
            new_post()
        elif menu == "Ask Firebox AI":
            firebox_ai()
        elif menu == "Logout":
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    else:
        auth_action = st.sidebar.radio("Account", ["Login", "Register"])
        if auth_action == "Login":
            login_user()
        else:
            register_user()

if __name__ == "__main__":
    main()
