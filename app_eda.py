import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase settings
# ---------------------
firebase_config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_PROJECT.firebaseapp.com",
    "databaseURL": "https://YOUR_PROJECT.firebaseio.com",
    "projectId": "YOUR_PROJECT",
    "storageBucket": "YOUR_PROJECT.appspot.com",
    "messagingSenderId": "YOUR_SENDER_ID",
    "appId": "YOUR_APP_ID"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# Session state initialization
# ---------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ''
    st.session_state.id_token = ''
    st.session_state.user_name = ''
    st.session_state.user_gender = 'None'
    st.session_state.user_phone = ''
    st.session_state.profile_image_url = ''

# ---------------------
# Home Page
# ---------------------
class Home:
    def __init__(self, login_page, register_page, reset_password_page):
        st.title("🏠 Home - Regional Population Analysis")
        if st.session_state.logged_in:
            st.success(f"Welcome, {st.session_state.user_email}")
        st.markdown(
            """
            **Dataset**: population_trends_english.csv  
            - **Columns**: Year, Region, Population, Births, Deaths  
            - **Description**: Annual population statistics by region
            """
        )

# ---------------------
# Login Page
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_data = firestore.child("users").child(email.replace('.', '_')).get().val()
                if user_data:
                    st.session_state.user_name = user_data.get('name', '')
                    st.session_state.user_gender = user_data.get('gender', 'None')
                    st.session_state.user_phone = user_data.get('phone', '')
                    st.session_state.profile_image_url = user_data.get('profile_image_url', '')

                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("Login failed. Please check your credentials.")

# ---------------------
# Registration Page
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["None", "Male", "Female"])
        phone = st.text_input("Phone Number")

        if st.button("Sign Up"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace('.', '_')).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("Registration successful! Redirecting to login...")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("Registration failed. Please try again.")

# ---------------------
# Password Reset Page
# ---------------------
class ResetPassword:
    def __init__(self):
        st.title("🔎 Reset Password")
        email = st.text_input("Email")
        if st.button("Send Reset Email"):
            try:
                auth.send_password_reset_email(email)
                st.success("Password reset email sent.")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("Failed to send reset email. Please try again.")

# ---------------------
# User Profile Page
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 My Profile")
        email = st.session_state.user_email
        new_email = st.text_input("Email", value=email)
        name = st.text_input("Name", value=st.session_state.user_name)
        gender = st.selectbox(
            "Gender",
            ["None", "Male", "Female"],
            index=["None", "Male", "Female"].index(st.session_state.user_gender)
        )
        phone = st.text_input("Phone Number", value=st.session_state.user_phone)
        uploaded_file = st.file_uploader("Upload Profile Image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.profile_image_url:
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("Save"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone
            firestore.child("users").child(new_email.replace('.', '_')).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.profile_image_url
            })
            st.success("Profile updated successfully.")
            time.sleep(1)
            st.rerun()

# ---------------------
# Logout Page
# ---------------------
class Logout:
    def __init__(self):
        for key in ['logged_in', 'user_email', 'id_token', 'user_name', 'user_gender', 'user_phone', 'profile_image_url']:
            st.session_state[key] = False if key == 'logged_in' else ''
        st.success("Logged out successfully.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA Page
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Regional Population Analysis EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload the population_trends.csv file.")
            return

        # Read CSV
        df = pd.read_csv(uploaded)
        # Translate Korean columns to English if present
        mapping = {
            '연도': 'Year',
            '지역': 'Region',
            '인구': 'Population',
            '출생아수(명)': 'Births',
            '사망자수(명)': 'Deaths'
        }
        df.rename(columns={k:v for k,v in mapping.items() if k in df.columns}, inplace=True)
        # Ensure numeric columns
        for col in ['Population', 'Births', 'Deaths']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        tabs = st.tabs([
            "1. Basic Stats", "2. Nationwide Trend", "3. 5-Year Change",
            "4. Top Changes", "5. Cumulative Area Chart"
        ])
        # 1. Basic Stats
        with tabs[0]:
            st.header("🔍 Basic Statistics")
            st.write(df.isnull().sum())
            st.write(f"Duplicate rows: {df.duplicated().sum()}")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())
            st.dataframe(df.describe())
            st.dataframe(df.head())
        # 2. Nationwide Trend
        with tabs[1]:
            st.header("📈 Yearly Population Trend (Nationwide)")
            trend = df[df['Region'] == 'Nationwide'].groupby('Year')['Population'].sum().reset_index()
            fig, ax = plt.subplots()
            sns.lineplot(x='Year', y='Population', data=trend, ax=ax)
            ax.set_title('Yearly Population Trend (Nationwide)')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)
        # 3. 5-Year Change
        with tabs[2]:
            st.header("📊 Population Change Over Last 5 Years")
            max_year = df['Year'].max()
            recent = df[df['Year'].between(max_year-4, max_year) & (df['Region'] != 'Nationwide')]
            pivot_df = recent.pivot(index='Region', columns='Year', values='Population')
            pivot_df['Change'] = pivot_df[max_year] - pivot_df[max_year-4]
            change_df = pivot_df['Change'].sort_values(ascending=False).reset_index()
            fig, ax = plt.subplots()
            sns.barplot(x='Change', y='Region', data=change_df, ax=ax)
            ax.set_title('Population Change in Last 5 Years')
            ax.set_xlabel('Change')
            ax.set_ylabel('Region')
            for i, v in enumerate(change_df['Change']):
                ax.text(v, i, str(v))
            st.pyplot(fig)
        # 4. Top Changes
        with tabs[3]:
            st.header("📋 Top Regions by Yearly Change")
            diff_df = df[df['Region'] != 'Nationwide'].copy()
            diff_df['Diff'] = diff_df.groupby('Region')['Population'].diff()
            top100 = diff_df.nlargest(100, 'Diff')[['Year','Region','Diff']]
            st.dataframe(top100.style.background_gradient(subset=['Diff'], cmap='Blues'))
        # 5. Cumulative Area Chart
        with tabs[4]:
            st.header("📊 Cumulative Area Chart")
            df_cum = df[df['Region'] != 'Nationwide']
            area_pivot = df_cum.pivot(index='Year', columns='Region', values='Population')
            fig, ax = plt.subplots()
            area_pivot.plot.area(ax=ax)
            ax.set_title('Population by Region Over Years')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)

# ---------------------
# Page Navigation
# ---------------------
Page_Login    = st.Page(Login, title="Login", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_Reset    = st.Page(ResetPassword, title="Reset Password", icon="🔎", url_path="reset-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_Reset), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Profile", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout, title="Logout", icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA, title="EDA", icon="📊", url_path="eda")

if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_Reset]

selected_page = st.navigation(pages)
selected_page.run()
