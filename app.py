import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Paths to user and post data
USER_FILE = "users.csv"
POST_FILE = "posts.csv"

# Create user & post files if not exist
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)

if not os.path.exists(POST_FILE):
    pd.DataFrame(columns=["username", "content", "timestamp", "likes", "comments"]).to_csv(POST_FILE, index=False)

# Session state to track login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ---------------- Registration Page ---------------- #
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

# ---------------- Login Page ---------------- #
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

# ---------------- Main Social Feed ---------------- #
def social_feed():
    st.title("🔥 Firebox Social")
    st.write(f"Logged in as **{st.session_state.username}**")

    # Post something
    post_text = st.text_area("What's on your mind?")
    if st.button("Post"):
        if post_text.strip():
            post_data = pd.read_csv(POST_FILE)
            new_post = {
                "username": st.session_state.username,
                "content": post_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "likes": 0,
                "comments": ""
            }
            post_data = pd.concat([post_data, pd.DataFrame([new_post])], ignore_index=True)
            post_data.to_csv(POST_FILE, index=False)
            st.success("Posted!")

    st.markdown("---")

    # View all posts
    post_data = pd.read_csv(POST_FILE)
    if post_data.empty:
        st.info("No posts yet. Be the first to post!")
    else:
        post_data = post_data.sort_values(by="timestamp", ascending=False)
        for idx, row in post_data.iterrows():
            st.markdown(f"**{row['username']}** posted at {row['timestamp']}")
            st.markdown(f"{row['content']}")
            st.markdown(f"❤️ {row['likes']} likes")
            
            # Like button
            if st.button(f"Like {idx}"):
                post_data.at[idx, 'likes'] += 1
                post_data.to_csv(POST_FILE, index=False)
                st.experimental_rerun()

            # Comment
            comment = st.text_input(f"Comment on post {idx}", key=f"comment_{idx}")
            if st.button(f"Add Comment {idx}"):
                if comment.strip():
                    current_comments = post_data.at[idx, 'comments']
                    new_comments = f"{current_comments} [{st.session_state.username}]: {comment} |"
                    post_data.at[idx, 'comments'] = new_comments
                    post_data.to_csv(POST_FILE, index=False)
                    st.experimental_rerun()

            # Show comments
            if row['comments']:
                st.markdown("*Comments:*")
                for comment_text in row['comments'].split("|"):
                    if comment_text.strip():
                        st.markdown(f"- {comment_text.strip()}")
            st.markdown("---")

# ---------------- Main App Flow ---------------- #
def main():
    st.title("🔥 Firebox — Social Media in Streamlit")
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

if __name__ == "__main__":
    main()
