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
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home - 지역별 인구 분석")
        if st.session_state.logged_in:
            st.success(f"{st.session_state.user_email}님, 환영합니다.")
        st.markdown(
            """
            ---
            **Dataset: population_trends.csv**  
            - **Columns**: `Year`, `Region`, `Population`, `Births`, `Deaths`  
            - **Description**: Annual population statistics by region
            """
        )

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
                info = firestore.child("users").child(email.replace('.', '_')).get().val()
                if info:
                    st.session_state.user_name = info.get("name", "")
                    st.session_state.user_gender = info.get("gender", "선택 안함")
                    st.session_state.user_phone = info.get("phone", "")
                    st.session_state.profile_image_url = info.get("profile_image_url", "")
                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"로그인 실패: {e}")

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
                firestore.child("users").child(email.replace('.', '_')).set({
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
            except Exception as e:
                st.error(f"회원가입 실패: {e}")

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
            except Exception as e:
                st.error(f"이메일 전송 실패: {e}")

# ---------------------
# 사용자 정보 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")
        email = st.session_state.user_email
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.user_name)
        options = ["선택 안함", "남성", "여성"]
        curr = st.session_state.user_gender
        if curr not in options:
            curr = "선택 안함"
        gender = st.selectbox("성별", options, index=options.index(curr))
        phone = st.text_input("휴대전화번호", value=st.session_state.user_phone)
        up = st.file_uploader("프로필 이미지 업로드", type=["jpg","jpeg","png"])
        if up:
            path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(path).put(up, st.session_state.id_token)
            url = storage.child(path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = url
            st.image(url, width=150)
        elif st.session_state.profile_image_url:
            st.image(st.session_state.profile_image_url, width=150)
        if st.button("수정"):
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
            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        for k in ['logged_in','user_email','id_token','user_name','user_gender','user_phone','profile_image_url']:
            st.session_state[k] = False if k=='logged_in' else ''
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Regional Population Analysis EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return
        df = pd.read_csv(uploaded)
        df.columns = df.columns.str.strip()
        col_map = {'연도':'Year','지역':'Region','인구':'Population','출생아수(명)':'Births','사망자수(명)':'Deaths'}
        df.rename(columns={k:v for k,v in col_map.items() if k in df.columns}, inplace=True)
        for c in ['Population','Births','Deaths']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        region_map = {
            '전국':'Nationwide','서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
            '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi',
            '강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
            '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
        }
        df['Region'] = df['Region'].map(region_map).fillna(df['Region'])
        tabs = st.tabs(["1. Basic Statistics","2. Nationwide Trend","3. 5-Year Change","4. Top Changes","5. Cumulative Area Chart"])
        with tabs[0]:
            st.header("🔍 Basic Statistics")
            st.write(df.isnull().sum())
            st.write(f"Duplicate rows: {df.duplicated().sum()}")
            buffer = io.StringIO(); df.info(buf=buffer); st.text(buffer.getvalue())
            st.dataframe(df.describe()); st.dataframe(df.head())
        with tabs[1]:
            st.header("📈 Yearly Population Trend (Nationwide)")
            trend = df[df['Region']=='Nationwide'].groupby('Year')['Population'].sum().reset_index()
            fig,ax = plt.subplots(); sns.lineplot(x='Year',y='Population',data=trend,ax=ax)
            ax.set_title('Yearly Population Trend (Nationwide)'); ax.set_xlabel('Year'); ax.set_ylabel('Population'); st.pyplot(fig)
        with tabs[2]:
            st.header("📊 Population Change in Last 5 Years")
            max_year = df['Year'].max()
            recent = df[df['Year'].between(max_year-4,max_year)&(df['Region']!='Nationwide')]
            pivot = recent.pivot(index='Region',columns='Year',values='Population')
            pivot['Change'] = pivot[max_year]-pivot[max_year-4]
            change = pivot['Change'].sort_values(ascending=False).reset_index()
            fig,ax=plt.subplots(); sns.barplot(x='Change',y='Region',data=change,ax=ax)
            ax.set_title('Population Change in Last 5 Years'); ax.set_xlabel('Change'); ax.set_ylabel('Region')
            for i,v in enumerate(change['Change']): ax.text(v,i,str(v))
            st.pyplot(fig)
        with tabs[3]:
            st.header("📋 Top Regions by Yearly Change")
            diff_df = df[df['Region']!='Nationwide'].copy(); diff_df['Diff']=diff_df.groupby('Region')['Population'].diff()
            top100 = diff_df.nlargest(100,'Diff')[['Year','Region','Diff']]
            st.dataframe(top100.style.background_gradient(subset=['Diff'],cmap='Blues'))
        with tabs[4]:
            st.header("📊 Cumulative Area Chart")
            area = df[df['Region']!='Nationwide'].pivot(index='Year',columns='Region',values='Population')
            fig,ax=plt.subplots(); area.plot.area(ax=ax)
            ax.set_title('Population by Region Over Years'); ax.set_xlabel('Year'); ax.set_ylabel('Population'); st.pyplot(fig)

# ---------------------
# 페이지 객체 생성 및 네비게이션
# ---------------------
Page_Login    = st.Page(Login, title="Login", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Profile", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout, title="Logout", icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA, title="EDA", icon="📊", url_path="eda")

if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
