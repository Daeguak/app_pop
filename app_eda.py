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
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
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
# Home page
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
            - **Description**: Annual population and demographic changes by region
            """
        )

# ---------------------
# Login page
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

                user_info = firestore.child("users").child(email.replace('.', '_')).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name","")
                    st.session_state.user_gender = user_info.get("gender","None")
                    st.session_state.user_phone = user_info.get("phone","")
                    st.session_state.profile_image_url = user_info.get("profile_image_url","")

                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Login failed")

# ---------------------
# Register page
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["None","Male","Female"])
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
            except:
                st.error("Registration failed")

# ---------------------
# Password reset page
# ---------------------
class ResetPassword:
    def __init__(self):
        st.title("🔎 Reset Password")
        email = st.text_input("Email")
        if st.button("Send Reset Email"):
            try:
                auth.send_password_reset_email(email)
                st.success("Reset email sent.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Failed to send reset email")

# ---------------------
# User profile page
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 My Profile")
        email = st.session_state.user_email
        new_email = st.text_input("Email", value=email)
        name = st.text_input("Name", value=st.session_state.user_name)
        gender = st.selectbox("Gender", ["None","Male","Female"], index=["None","Male","Female"].index(st.session_state.user_gender))
        phone = st.text_input("Phone Number", value=st.session_state.user_phone)
        file = st.file_uploader("Upload Profile Image", type=["jpg","jpeg","png"])
        if file:
            path = f"profiles/{email.replace('.','_')}.jpg"
            storage.child(path).put(file, st.session_state.id_token)
            url = storage.child(path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = url
            st.image(url,width=150)
        elif st.session_state.profile_image_url:
            st.image(st.session_state.profile_image_url,width=150)
        if st.button("Save"):
            st.session_state.user_email=new_email
            st.session_state.user_name=name
            st.session_state.user_gender=gender
            st.session_state.user_phone=phone
            firestore.child("users").child(new_email.replace('.','_')).update({
                "email":new_email,
                "name":name,
                "gender":gender,
                "phone":phone,
                "profile_image_url":st.session_state.profile_image_url
            })
            st.success("Profile updated.")
            time.sleep(1)
            st.rerun()

# ---------------------
# Logout page
# ---------------------
class Logout:
    def __init__(self):
        for key in ['logged_in','user_email','id_token','user_name','user_gender','user_phone','profile_image_url']:
            st.session_state[key]=False if key=='logged_in' else ''
        st.success("Logged out.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA page
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Regional Population Analysis EDA")
        uploaded=st.file_uploader("Upload population_trends_english.csv",type="csv")
        if not uploaded:
            st.info("Upload the population_trends_english.csv file.")
            return
        df=pd.read_csv(uploaded)
        # Ensure columns and region names are in English
        df=df.rename(columns={'Year':'Year','Region':'Region','Population':'Population','Births':'Births','Deaths':'Deaths'})
        # Convert numeric columns
        for c in ['Population','Births','Deaths']:
            df[c]=pd.to_numeric(df[c],errors='coerce').fillna(0).astype(int)
        tabs=st.tabs(["1.Basic Stats","2.Nationwide Trend","3.5-Year Change","4.Top Changes","5.Cumulative Area Chart"])
        with tabs[0]:
            st.header("🔍 Basic Statistics")
            st.write(df.isnull().sum())
            st.write(f"Duplicate rows: {df.duplicated().sum()}")
            buf=io.StringIO();df.info(buf=buf);st.text(buf.getvalue())
            st.dataframe(df.describe());st.dataframe(df.head())
        with tabs[1]:
            st.header("📈 Yearly Population Trend (Nationwide)")
            tot=df[df['Region']=='Nationwide'].groupby('Year')['Population'].sum().reset_index()
            fig,ax=plt.subplots();sns.lineplot(x='Year',y='Population',data=tot,ax=ax)
            ax.set_title('Yearly Population Trend (Nationwide)');ax.set_xlabel('Year');ax.set_ylabel('Population');st.pyplot(fig)
        with tabs[2]:
            st.header("📊 Population Change Over Last 5 Years")
            ly=df['Year'].max();recent=df[df['Year'].between(ly-4,ly)&(df['Region']!='Nationwide')]
            piv=recent.pivot(index='Region',columns='Year',values='Population');piv['Change']=piv[ly]-piv[ly-4]
            ch=piv['Change'].sort_values(ascending=False).reset_index();fig,ax=plt.subplots();sns.barplot(x='Change',y='Region',data=ch,ax=ax)
            ax.set_title('Population Change in Last 5 Years');ax.set_xlabel('Change');ax.set_ylabel('Region');
            for i,v in enumerate(ch['Change']):ax.text(v,i,f"{v}");st.pyplot(fig)
        with tabs[3]:
            st.header("📋 Top Regions by Yearly Change")
            dff=df[df['Region']!='Nationwide'].copy();dff['diff']=dff.groupby('Region')['Population'].diff()
            top=dff.nlargest(100,'diff')[['Year','Region','diff']];st.dataframe(top.style.background_gradient(subset=['diff'],cmap='Blues'))
        with tabs[4]:
            st.header("📊 Cumulative Area Chart")
            dr=df[df['Region']!='Nationwide'];ap=dr.pivot(index='Year',columns='Region',values='Population')
            fig,ax=plt.subplots();ap.plot.area(ax=ax)
            ax.set_title('Population by Region Over Years');ax.set_xlabel('Year');ax.set_ylabel('Population');st.pyplot(fig)

# ---------------------
# Page navigation setup
# ---------------------
Page_Login=st.Page(Login,title="Login",icon="🔐",url_path="login")
Page_Register=st.Page(lambda:Register(Page_Login.url_path),title="Register",icon="📝",url_path="register")
Page_Reset=st.Page(ResetPassword,title="Reset Password",icon="🔎",url_path="reset-password")
Page_Home=st.Page(lambda:Home(Page_Login,Page_Register,Page_Reset),title="Home",icon="🏠",url_path="home",default=True)
Page_User=st.Page(UserInfo,title="My Profile",icon="👤",url_path="user-info")
Page_Logout=st.Page(Logout,title="Logout",icon="🔓",url_path="logout")
Page_EDA=st.Page(EDA,title="EDA",icon="📊",url_path="eda")
if st.session_state.logged_in:
    pages=[Page_Home,Page_User,Page_Logout,Page_EDA]
else:
    pages=[Page_Home,Page_Login,Page_Register,Page_Reset]
sel=st.navigation(pages)
sel.run()
