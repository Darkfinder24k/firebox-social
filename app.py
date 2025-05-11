import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# ---------- Quantora Social Configuration ----------
QUANTORA_POSTS_CSV = "quantora_social_posts.csv"
QUANTORA_USERS_CSV = "quantora_social_users.csv"
QUANTORA_FOLLOWS_CSV = "quantora_social_follows.csv"
QUANTORA_IMAGES_DIR = "quantora_social_images"
QUANTORA_PROFILE_PICS_DIR = "quantora_social_profile_pics"
DEFAULT_PROFILE_PIC = "default_profile.png"

if not os.path.exists(QUANTORA_POSTS_CSV):
    quantora_df_posts = pd.DataFrame(columns=['quantora_username', 'quantora_timestamp', 'quantora_text', 'quantora_image_path', 'quantora_likes', 'quantora_comments'])
    quantora_df_posts.to_csv(QUANTORA_POSTS_CSV, index=False)

if not os.path.exists(QUANTORA_USERS_CSV):
    quantora_df_users = pd.DataFrame(columns=['quantora_email', 'quantora_username', 'quantora_password', 'quantora_profile_pic', 'bio'])
    quantora_df_users.to_csv(QUANTORA_USERS_CSV, index=False)

if not os.path.exists(QUANTORA_FOLLOWS_CSV):
    quantora_df_follows = pd.DataFrame(columns=['follower', 'followed'])
    quantora_df_follows.to_csv(QUANTORA_FOLLOWS_CSV, index=False)

if not os.path.exists(QUANTORA_IMAGES_DIR):
    os.makedirs(QUANTORA_IMAGES_DIR)

if not os.path.exists(QUANTORA_PROFILE_PICS_DIR):
    os.makedirs(QUANTORA_PROFILE_PICS_DIR)

# --- Helper Functions ---
def handle_hashtags(text):
    # Basic implementation: returns the text as is
    return text

def quantora_user_info_header(username, show_follow=False):
    quantora_users_df = pd.read_csv(QUANTORA_USERS_CSV)
    try:
        quantora_user_data = quantora_users_df[quantora_users_df['quantora_username'] == username].iloc[0]
        quantora_profile_pic_path = quantora_user_data.get('quantora_profile_pic', DEFAULT_PROFILE_PIC)
        if not os.path.exists(quantora_profile_pic_path):
            quantora_profile_pic_path = DEFAULT_PROFILE_PIC
    except IndexError:
        quantora_profile_pic_path = DEFAULT_PROFILE_PIC

    col1, col2 = st.columns([0.08, 0.92])
    with col1:
        st.markdown(f'<img src="{quantora_profile_pic_path}" width="36" style="border-radius: 50%; object-fit: cover;">', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<strong style='font-size: 1.1em;'>{username}</strong>", unsafe_allow_html=True)
        if show_follow and username != st.session_state.quantora_username:
            is_following = is_user_following(st.session_state.quantora_username, username)
            follow_text = "Following" if is_following else "Follow"
            if st.button(follow_text, key=f"follow_{username}", use_container_width=True):
                update_follow(st.session_state.quantora_username, username, not is_following)
                st.rerun()

def quantora_post_actions(row, index):
    quantora_username = row['quantora_username']
    quantora_timestamp = row['quantora_timestamp']
    quantora_likes = int(row.get('quantora_likes', 0))
    quantora_post_key = f"{quantora_username}_{quantora_timestamp}"
    liked = quantora_post_key in st.session_state.quantora_liked_posts

    col1, col2, _ = st.columns([0.15, 0.15, 0.7])
    with col1:
        like_button_label = f"{'❤️' if liked else '🤍'} {quantora_likes}"
        if st.button(like_button_label, key=f"like_btn_{index}", use_container_width=True):
            quantora_df = pd.read_csv(QUANTORA_POSTS_CSV)
            if liked:
                quantora_df.at[index, 'quantora_likes'] -= 1
                st.session_state.quantora_liked_posts.discard(quantora_post_key)
            else:
                quantora_df.at[index, 'quantora_likes'] += 1
                st.session_state.quantora_liked_posts.add(quantora_post_key)
            quantora_df.to_csv(QUANTORA_POSTS_CSV, index=False)
            st.rerun()
    with col2:
        with st.expander("💬 Comments", expanded=False):
            quantora_comment_section(row, index)

def quantora_comment_section(row, index):
    quantora_username = row['quantora_username']
    quantora_comments_raw = row.get('quantora_comments', '')
    if pd.isna(quantora_comments_raw):
        quantora_comments_raw = ""
    quantora_comments = quantora_comments_raw.split("|") if quantora_comments_raw else []
    for c in quantora_comments:
        if c:
            parts = c.split(": ", 1)
            if len(parts) == 2:
                commenter, comment_text = parts[0], parts[1]
                colored_commenter = f'<span style="color: black;">{commenter}:</span>' # Commenter name in black
                colored_comment_text = f'<span style="color: black;">{comment_text}</span>' # Comment text in black
                st.markdown(f"<div style='padding: 8px; margin-bottom: 5px; background-color: #f0f2f5; border-radius: 5px;'><strong>{colored_commenter}</strong> {colored_comment_text}</div>", unsafe_allow_html=True)
            else:
                colored_c = f'<span style="color: black;">{c}</span>' # Single-part comments in black
                st.markdown(f"- {colored_c}", unsafe_allow_html=True)

    comment_input_col, comment_button_col = st.columns([0.8, 0.2])
    with comment_input_col:
        quantora_new_comment = st.text_input("", placeholder="Add a comment...", key=f"comment_input_{index}")
    with comment_button_col:
        if st.button("Post", key=f"comment_post_btn_{index}", use_container_width=True):
            if quantora_new_comment:
                quantora_df = pd.read_csv(QUANTORA_POSTS_CSV)
                colored_username = f'<span style="color: black;">{st.session_state.quantora_username}:</span>' # Your username in black
                colored_new_comment = f'<span style="color: black;">{quantora_new_comment}</span>' # New comment in black
                quantora_updated_comment = f"{st.session_state.quantora_username}: {quantora_new_comment}" # Saving plain text
                quantora_combined_comments = quantora_comments_raw + f"|{quantora_updated_comment}" if quantora_comments_raw else quantora_updated_comment
                quantora_df.at[index, 'quantora_comments'] = quantora_combined_comments
                quantora_df.to_csv(QUANTORA_POSTS_CSV, index=False)
                st.rerun()

def is_user_following(follower, followed):
    try:
        follows_df = pd.read_csv(QUANTORA_FOLLOWS_CSV)
        return ((follows_df['follower'] == follower) & (follows_df['followed'] == followed)).any()
    except FileNotFoundError:
        return False

def update_follow(follower, followed, follow=True):
    follows_df = pd.read_csv(QUANTORA_FOLLOWS_CSV) if os.path.exists(QUANTORA_FOLLOWS_CSV) else pd.DataFrame(columns=['follower', 'followed'])
    if follow:
        if not ((follows_df['follower'] == follower) & (follows_df['followed'] == followed)).any():
            new_follow = pd.DataFrame([[follower, followed]], columns=['follower', 'followed'])
            new_follow.to_csv(QUANTORA_FOLLOWS_CSV, mode='a', header=False, index=False)
    else:
        follows_df = follows_df[~((follows_df['follower'] == follower) & (follows_df['followed'] == followed))]
        follows_df.to_csv(QUANTORA_FOLLOWS_CSV, index=False)

def search_users(query):
    users_df = pd.read_csv(QUANTORA_USERS_CSV)
    results = users_df[users_df['quantora_username'].str.contains(query, case=False)]
    return results

def get_user_posts(username):
    posts_df = pd.read_csv(QUANTORA_POSTS_CSV)
    return posts_df[posts_df['quantora_username'] == username].sort_values(by='quantora_timestamp', ascending=False)

def get_followers(username):
    follows_df = pd.read_csv(QUANTORA_FOLLOWS_CSV) if os.path.exists(QUANTORA_FOLLOWS_CSV) else pd.DataFrame(columns=['follower', 'followed'])
    return follows_df[follows_df['followed'] == username]['follower'].tolist()

def get_following(username):
    follows_df = pd.read_csv(QUANTORA_FOLLOWS_CSV) if os.path.exists(QUANTORA_FOLLOWS_CSV) else pd.DataFrame(columns=['follower', 'followed'])
    return follows_df[follows_df['follower'] == username]['followed'].tolist()

# ---------- Quantora Social User Auth (Simplified & Persistent) ----------
def quantora_register_user():
    st.subheader("Join the Quantora Universe!")
    quantora_email = st.text_input("Your Email (optional)")
    quantora_username = st.text_input("Choose a Username")
    quantora_password = st.text_input("Create a Password", type="password")
    quantora_bio = st.text_area("Tell us about yourself (optional)")
    quantora_profile_pic_upload = st.file_uploader("Add a Profile Picture (optional)", type=["jpg", "jpeg", "png"])

    if st.button("Embark on Your Quantora Journey"):
        quantora_users_df = pd.read_csv(QUANTORA_USERS_CSV)
        if quantora_username in quantora_users_df['quantora_username'].values:
            st.error("This username is already taken. Let your uniqueness shine with another!")
        elif not quantora_username:
            st.error("A username is your key to the Quantora Universe!")
        elif not quantora_password:
            st.error("Set a password to secure your Quantora experience!")
        else:
            quantora_profile_pic_path = DEFAULT_PROFILE_PIC
            if quantora_profile_pic_upload is not None:
                pic_filename = f"{quantora_username}_{int(time.time())}_{quantora_profile_pic_upload.name}"
                quantora_profile_pic_path = os.path.join(QUANTORA_PROFILE_PICS_DIR, pic_filename)
                with open(quantora_profile_pic_path, "wb") as f:
                    f.write(quantora_profile_pic_upload.getbuffer())

            quantora_new_user = pd.DataFrame([[quantora_email, quantora_username, quantora_password, quantora_profile_pic_path, quantora_bio]],
                                        columns=['quantora_email', 'quantora_username', 'quantora_password', 'quantora_profile_pic', 'bio'])
            quantora_new_user.to_csv(QUANTORA_USERS_CSV, mode='a', header=False, index=False)
            st.success("Welcome to Quantora! Log in to begin your adventure.")

def quantora_login_user():
    st.subheader("Re-enter the Quantora Universe")
    quantora_username = st.text_input("Username")
    quantora_password = st.text_input("Password", type="password")
    if st.button("Unlock Quantora"):
        quantora_users_df = pd.read_csv(QUANTORA_USERS_CSV)
        user_match = quantora_users_df[
            (quantora_users_df['quantora_username'] == quantora_username) &
            (quantora_users_df['quantora_password'] == quantora_password)
        ]
        if not user_match.empty:
            st.session_state.quantora_logged_in = True
            st.session_state.quantora_username = quantora_username
            st.success(f"Welcome back, @{quantora_username}! The Quantora Universe awaits.")
            st.rerun()
        else:
            st.error("Incorrect username or password. Double-check your credentials to rejoin Quantora.")

# ---------- Quantora Social Post Creation ----------
def quantora_new_post():
    st.subheader("Share Your Moment on Quantora")
    quantora_post_text = st.text_area("What's happening?", height=150)
    quantora_uploaded_file = st.file_uploader("Add a Photo or Video (optional)", type=["jpg", "jpeg", "png"]) # Consider adding video later

    if st.button("Post to Quantora"):
        quantora_image_path = ""
        if quantora_uploaded_file is not None:
            image_filename = f"{st.session_state.quantora_username}_{int(time.time())}_{quantora_uploaded_file.name}"
            quantora_image_path = os.path.join(QUANTORA_IMAGES_DIR, image_filename)
            with open(quantora_image_path, "wb") as f:
                f.write(quantora_uploaded_file.getbuffer())

        quantora_new_data = pd.DataFrame([[st.session_state.quantora_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quantora_post_text, quantora_image_path, 0, ""]],
                                    columns=['quantora_username', 'quantora_timestamp', 'quantora_text', 'quantora_image_path', 'quantora_likes', 'quantora_comments'])
        quantora_new_data.to_csv(QUANTORA_POSTS_CSV, mode='a', header=False, index=False)
        st.success("Your post has been shared with the Quantora community!")
        st.rerun()

# ---------- Quantora Social Feed Display (See Everyone's Posts) ----------
def quantora_social_feed():
    st.subheader("Your Quantora Feed")
    try:
        quantora_df = pd.read_csv(QUANTORA_POSTS_CSV)
        all_posts = quantora_df.sort_values(by='quantora_timestamp', ascending=False)
        for index, row in all_posts.iterrows():
            st.markdown("<div style='margin-bottom: 20px; padding: 15px; border: 1px solid #e1e4e8; border-radius: 10px; background-color: #fff;'>", unsafe_allow_html=True)
            quantora_user_info_header(row['quantora_username'])
            st.markdown(f"<div style='margin-top: 10px; font-size: 1em; line-height: 1.4;'>{handle_hashtags(row.get('quantora_text', ''))}</div>", unsafe_allow_html=True)
            image_path = row.get('quantora_image_path')
            if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                st.image(image_path, use_column_width=True, style="margin-top: 10px; border-radius: 8px;")
            st.markdown("<hr style='margin: 15px 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
            quantora_post_actions(row, index)
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading feed: {e}")

# ---------- Quantora Social Profile Page (Enhanced & Error Handling) ----------
def quantora_profile(view_username=None):
    username_to_view = view_username if view_username else st.session_state.quantora_username
    st.subheader(f"@{username_to_view}")

    try:
        user_data = pd.read_csv(QUANTORA_USERS_CSV)
        user_profile = user_data[user_data['quantora_username'] == username_to_view].iloc[0]
        bio= user_profile.get('bio', 'No bio available.')
        profile_pic = user_profile.get('quantora_profile_pic', DEFAULT_PROFILE_PIC)
        followers = get_followers(username_to_view)
        following = get_following(username_to_view)
        posts = get_user_posts(username_to_view)

        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            st.markdown(f'<img src="{profile_pic}" width="80" style="border-radius: 50%; object-fit: cover;">', unsafe_allow_html=True)
        with col2:
            st.markdown(f"<strong style='font-size: 1.5em;'>{username_to_view}</strong>", unsafe_allow_html=True)
            st.markdown(f"<span style='color: #777;'>{len(posts)} posts | {len(followers)} followers | {len(following)} following</span>", unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top: 5px;'>{bio}</p>", unsafe_allow_html=True)
            if username_to_view != st.session_state.quantora_username:
                is_following = is_user_following(st.session_state.quantora_username, username_to_view)
                follow_text = "Following" if is_following else "Follow"
                if st.button(follow_text, key=f"profile_follow_{username_to_view}", use_container_width=True):
                    update_follow(st.session_state.quantora_username, username_to_view, not is_following)
                    st.rerun()

        st.subheader("Posts")
        if not posts.empty:
            cols = st.columns(3)
            for i, row in posts.iterrows():
                with cols[i % 3]:
                    if row['quantora_image_path'] and os.path.exists(row['quantora_image_path']):
                        st.image(row['quantora_image_path'], use_column_width=True, style="border-radius: 5px;")
                    else:
                        st.info("No image") # Placeholder for text posts in grid
        else:
            st.info(f"@{username_to_view} hasn't posted yet.")

    except IndexError:
        st.error(f"User @{username_to_view} not found.")
    except FileNotFoundError:
        st.error("User data file not found.")
    except Exception as e:
        st.error(f"An error occurred while loading the profile: {e}")

# ---------- Quantora Social Search ----------
def quantora_search():
    st.subheader("Search Users")
    query = st.text_input("Search for usernames:")
    if query:
        results = search_users(query)
        if not results.empty:
            for index, user in results.iterrows():
                if st.button(f"@{user['quantora_username']}", key=f"search_result_{index}"):
                    st.session_state.view_profile = user['quantora_username']
                    st.rerun()
        else:
            st.info("No users found matching your search.")
    if 'view_profile' in st.session_state:
        quantora_profile(st.session_state.view_profile)
        if st.button("Back to Search"):
            del st.session_state.view_profile
            st.rerun()

# ---------- Quantora Social Navigation ----------
def quantora_sidebar():
    st.sidebar.title("✨ The Quantora Universe")
    if st.session_state.quantora_logged_in:
        st.sidebar.success(f"Navigating as @{st.session_state.quantora_username}")
        menu = st.sidebar.radio("Explore the Universe", ["Your Feed", "Create Post", "Your Profile", "Search", "Logout"]) # Simplified menu
        return menu
    else:
        st.sidebar.info("Embark on a new social journey with Quantora!")
        auth_action = st.sidebar.radio("Your Gateway", ["Log In", "Join Quantora"])
        return auth_action

# ---------- Main Quantora Social App ----------
def quantora_main():
    st.set_page_config(page_title="Quantora Social", layout="wide")

    if 'quantora_logged_in' not in st.session_state:
        st.session_state.quantora_logged_in = False
    if 'quantora_liked_posts' not in st.session_state:
        st.session_state.quantora_liked_posts = set()
    if 'view_profile' not in st.session_state:
        st.session_state.view_profile = None

    navigation = quantora_sidebar()

    if st.session_state.quantora_logged_in:
        if navigation == "Your Feed":
            quantora_social_feed()
        elif navigation == "Create Post":
            quantora_new_post()
        elif navigation == "Your Profile":
            quantora_profile()
        elif navigation == "Search":
            quantora_search()
        elif navigation == "Logout":
            st.session_state.quantora_logged_in = False
            st.session_state.quantora_username = ""
            st.session_state.view_profile = None
            st.rerun()
    else:
        if navigation == "Log In":
            quantora_login_user()
        elif navigation == "Join Quantora":
            quantora_register_user()

    # Persistent Login Check on App Start
    if 'quantora_logged_in' in st.session_state and st.session_state.quantora_logged_in:
        pass # User is already logged in

if __name__ == "__main__":
    quantora_main()
