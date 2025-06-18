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
        st.title("🏠 Home - Regional Population Analysis")
        if st.session_state.logged_in:
            st.success(f"{st.session_state.user_email}, welcome!")
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
        st.title("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
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
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["선택 안함", "Male", "Female"])
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
            except Exception as e:
                st.error(f"Registration failed: {e}")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 Reset Password")
        email = st.text_input("Email")
        if st.button("Send reset email"):
            try:
                auth.send_password_reset_email(email)
                st.success("Password reset email sent.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Reset failed: {e}")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 User Profile")
        email = st.session_state.user_email
        new_email = st.text_input("Email", value=email)
        name = st.text_input("Name", value=st.session_state.user_name)
        options = ["선택 안함", "Male", "Female"]
        curr = st.session_state.user_gender
        if curr not in options:
            curr = "선택 안함"
        gender = st.selectbox("Gender", options, index=options.index(curr))
        phone = st.text_input("Phone Number", value=st.session_state.user_phone)
        up = st.file_uploader("Profile Image", type=["jpg","jpeg","png"])
        if up:
            path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(path).put(up, st.session_state.id_token)
            url = storage.child(path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = url
            st.image(url, width=150)
        elif st.session_state.profile_image_url:
            st.image(st.session_state.profile_image_url, width=150)
        if st.button("Update Profile"):
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
            st.success("Profile updated.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        for k in ['logged_in','user_email','id_token','user_name','user_gender','user_phone','profile_image_url']:
            st.session_state[k] = False if k=='logged_in' else ''
        st.success("Logged out.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 EDA - Regional Population")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload the CSV file.")
            return

        # Load data
        df = pd.read_csv(uploaded)
        # 1. Replace '-' with 0 for Sejong region
        sejong_mask = df['지역'] == '세종'
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df.loc[sejong_mask, col] = df.loc[sejong_mask, col].replace('-', 0)
        # 2. Convert to numeric
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        # Column mapping
        df.columns = df.columns.str.strip()
        col_map = {'연도':'Year','지역':'Region','인구':'Population','출생아수(명)':'Births','사망자수(명)':'Deaths'}
        df.rename(columns=col_map, inplace=True)
        # Region translation
        region_map = {
            '전국':'Nationwide','서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
            '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi',
            '강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
            '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
        }
        df['Region'] = df['Region'].map(region_map).fillna(df['Region'])

        # Tabs
        tabs = st.tabs(["Basic Stats","Yearly Trend","Regional Analysis","Change Analysis","Visualization"])
        # 1. Basic Stats
        with tabs[0]:
            st.header("Basic Statistics")
            st.write(df.isnull().sum())
            st.write(f"Duplicates: {df.duplicated().sum()}")
            buf = io.StringIO(); df.info(buf=buf); st.text(buf.getvalue())
            st.dataframe(df.describe())
        # 2. Yearly Trend with Forecast
        with tabs[1]:
            st.header("Yearly Population Trend with 2035 Forecast")
            nation = df[df['Region']=='Nationwide']
            yearly = nation.groupby('Year')['Population'].sum().reset_index()
            # Forecast based on last 3 years
            last_year = yearly['Year'].max()
            last3 = nation[nation['Year'].between(last_year-2, last_year)]
            avg_net = (last3['Births'].sum() - last3['Deaths'].sum()) / 3
            last_pop = int(yearly.loc[yearly['Year']==last_year, 'Population'])
            future_years = list(range(last_year+1, 2036))
            future_pops = [last_pop + avg_net*(yr-last_year) for yr in future_years]
            forecast = pd.DataFrame({'Year': future_years, 'Population': future_pops})
            full = pd.concat([yearly, forecast], ignore_index=True)
            fig, ax = plt.subplots(figsize=(8,5))
            sns.lineplot(data=full, x='Year', y='Population', marker='o', ax=ax)
            ax.axvline(2035, ls='--', color='gray')
            ax.set_title('Yearly Population Trend with 2035 Forecast')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.annotate('Forecast', xy=(2035, full.query('Year==2035')['Population'].values[0]),
                        xytext=(last_year, full['Population'].max()*0.9),
                        arrowprops=dict(arrowstyle='->'))
            st.pyplot(fig)
        # 3. Regional Analysis
        with tabs[2]:
            st.header("Population Change in Last 5 Years by Region")
            max_year = df['Year'].max()
            recent = df[df['Year'].between(max_year-4, max_year) & (df['Region']!='Nationwide')]
            pivot = recent.pivot(index='Region', columns='Year', values='Population')
            pivot['Change'] = pivot[max_year] - pivot[max_year-4]
            pivot['Percent Change'] = pivot['Change'] / pivot[max_year-4] * 100
            pivot['Change_k'] = pivot['Change']/1000
            fig, axes = plt.subplots(ncols=2, figsize=(12,6))
            abs_df = pivot.reset_index().sort_values('Change_k', ascending=False)
            sns.barplot(x='Change_k', y='Region', data=abs_df, ax=axes[0])
            axes[0].set_title('Population Change (Thousands)')
            axes[0].set_xlabel('Change (Thousands)')
            pct_df = pivot.reset_index().sort_values('Percent Change', ascending=False)
            sns.barplot(x='Percent Change', y='Region', data=pct_df, ax=axes[1])
            axes[1].set_title('Percent Change (%)')
            axes[1].set_xlabel('Percent Change (%)')
            st.pyplot(fig)
            st.markdown("""
                **Analysis:** The left chart shows absolute changes over the last five years in thousands,
                highlighting which regions grew most in population. The right chart shows relative percent changes.
            """)
        # 4. Change Analysis
        with tabs[3]:
            st.header("Top 100 Yearly Population Changes")
            diff_df = df[df['Region']!='Nationwide'].copy()
            diff_df['Diff'] = diff_df.groupby('Region')['Population'].diff()
            top100 = diff_df.nlargest(100,'Diff')[['Year','Region','Diff']]
            styled = (top100.style.format({'Diff':'{:,}'})
                .background_gradient(cmap='bwr', subset=['Diff'])
            )
            st.dataframe(styled)
        # 5. Visualization
        with tabs[4]:
            st.header("Cumulative Area Chart by Region")
            area_df = df[df['Region']!='Nationwide'].pivot(index='Year', columns='Region', values='Population')
            colors = sns.color_palette('tab20', n_colors=area_df.shape[1])
            fig, ax = plt.subplots(figsize=(10,6))
            area_df.plot.area(ax=ax, color=colors)
            ax.set_title('Population by Region Over Years')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend(title='Region', bbox_to_anchor=(1.05,1), loc='upper left')
            st.pyplot(fig)

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