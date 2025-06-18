import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
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
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스 (수정)
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home - Regional Population Analysis")
        if st.session_state.get('logged_in'):
            st.success(f"Welcome, {st.session_state.get('user_email')}")

        st.markdown("""
        ---
        **Dataset: population_trends.csv**  
        - **Columns**: `Year`, `Region`, `Population`, `Births`, `Deaths`  
        - **Description**: Annual population and demographic changes by region
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스 (수정)
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Regional Population Analysis EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload the population_trends.csv file.")
            return

        df = pd.read_csv(uploaded)
        # Basic preprocessing
        df.loc[df['지역']=='세종', ['인구','출생아수(명)','사망자수(명)']] = \
            df[df['지역']=='세종'][['인구','출생아수(명)','사망자수(명)']].replace('-', 0)
        for col in ['인구','출생아수(명)','사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        tabs = st.tabs([
            "1. Basic Stats",
            "2. Nationwide Trend",
            "3. 5-Year Change",
            "4. Top Changes",
            "5. Cumulative Area Chart"
        ])

        # 1. Basic Stats
        with tabs[0]:
            st.header("🔍 Basic Statistics")
            st.subheader("Missing Values & Duplicates")
            missing = df.isnull().sum()
            st.write(missing)
            duplicates = df.duplicated().sum()
            st.write(f"Duplicate rows: {duplicates}")
            st.subheader("Data Structure & Summary")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())
            st.subheader("Sample Data")
            st.dataframe(df.head())

        # 2. Nationwide Trend
        with tabs[1]:
            st.header("📈 Yearly Population Trend (Nationwide)")
            total = df[df['지역']=='전국'].groupby('연도')['인구'].sum().reset_index()
            fig, ax = plt.subplots()
            sns.lineplot(x='연도', y='인구', data=total, ax=ax)
            ax.set_title('Yearly Population Trend (Nationwide)')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)

        # 3. 5-Year Change
        with tabs[2]:
            st.header("📊 Population Change Over Last 5 Years")
            last = df['연도'].max()
            recent = df[df['연도'].between(last-4, last) & (df['지역']!='전국')]
            pivot = recent.pivot(index='지역', columns='연도', values='인구')
            pivot['Change'] = pivot[last] - pivot[last-4]
            change = pivot['Change'].sort_values(ascending=False).reset_index()
            fig, ax = plt.subplots()
            sns.barplot(x='Change', y='지역', data=change, ax=ax)
            ax.set_title('Population Change in Last 5 Years')
            ax.set_xlabel('Change')
            ax.set_ylabel('Region')
            for i, v in enumerate(change['Change']):
                ax.text(v, i, f"{v}")
            st.pyplot(fig)

        # 4. Top Changes
        with tabs[3]:
            st.header("📋 Top Regions by Yearly Change")
            diff_df = df[df['지역']!='전국'].copy()
            diff_df['diff'] = diff_df.groupby('지역')['인구'].diff()
            top100 = diff_df.nlargest(100, 'diff')[['연도','지역','diff']]
            st.dataframe(top100.style.background_gradient(subset=['diff'], cmap='Blues'))

        # 5. Cumulative Area Chart
        with tabs[4]:
            st.header("📊 Cumulative Area Chart")
            df_region = df[df['지역']!='전국']
            pivot2 = df_region.pivot(index='연도', columns='지역', values='인구')
            fig, ax = plt.subplots()
            pivot2.plot.area(ax=ax)
            ax.set_title('Population by Region Over Years')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            st.pyplot(fig)

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()