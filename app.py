import streamlit as st
import sqlite3
import pdfplumber
import pandas as pd
import hashlib
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import docx
import pytesseract
from PIL import Image
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI HR System", layout="wide")

st.markdown("""
<style>
.main {background:#0e1117;color:white;}
.stButton>button {background:#4CAF50;color:white;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

st.title("🚀 AI HR Recruitment System (Final Boss)")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("system.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)")
c.execute("""CREATE TABLE IF NOT EXISTS candidates (
    name TEXT,
    resume TEXT,
    status TEXT,
    file_hash TEXT UNIQUE
)""")
conn.commit()

# ---------------- FILE HANDLING ----------------
def get_hash(file):
    b = file.read()
    file.seek(0)
    return hashlib.md5(b).hexdigest()

def extract_text(file):
    ext = file.name.split(".")[-1].lower()

    if ext == "pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text += p.extract_text() or ""
        return text

    elif ext == "docx":
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif ext in ["png","jpg","jpeg"]:
        return pytesseract.image_to_string(Image.open(file))

    return ""

# ---------------- AI ----------------
def detect_fake(text):
    if len(text.split()) < 50:
        return "⚠️ Suspicious"
    return "✅ Genuine"

def feedback(score):
    if score > 75: return "Excellent candidate"
    elif score > 50: return "Good candidate"
    elif score > 30: return "Average match"
    return "Weak candidate"

def extract_skills(text):
    keywords = ["python","java","sql","machine","data","analysis","react","flutter","ai"]
    found = [k for k in keywords if k in text.lower()]
    return found

# ---------------- LOGIN ----------------
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    mode = st.radio("Login/Register", ["Login","Register"])

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if mode == "Register":
        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)",(u,p))
                conn.commit()
                st.success("Created")
            except:
                st.error("Exists")

    else:
        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
            if c.fetchone():
                st.session_state.login=True
                st.rerun()
            else:
                st.error("Invalid")

    st.stop()

# ---------------- NAV ----------------
page = st.sidebar.radio("Menu", ["Dashboard","Upload","Screening","Analytics","Database"])

# ---------------- DASHBOARD ----------------
if page=="Dashboard":
    c.execute("SELECT COUNT(*) FROM candidates")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM candidates WHERE status='employed'")
    hired = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM candidates WHERE status='rejected'")
    rejected = c.fetchone()[0]

    col1,col2,col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("Hired", hired)
    col3.metric("Rejected", rejected)

# ---------------- UPLOAD ----------------
elif page=="Upload":
    file = st.file_uploader("Upload Resume", type=["pdf","docx","png","jpg","jpeg"])

    if file:
        h = get_hash(file)
        text = extract_text(file)

        if not text.strip():
            st.error("No readable text")
        else:
            c.execute("SELECT * FROM candidates WHERE file_hash=?",(h,))
            if c.fetchone():
                st.error("Duplicate ❌")
            else:
                c.execute("INSERT INTO candidates VALUES (?,?,?,?)",(file.name,text,"pending",h))
                conn.commit()
                st.success("Uploaded ✔")
                st.text_area("Preview", text[:1000])

# ---------------- SCREENING ----------------
elif page=="Screening":
    job = st.text_area("Job Description")

    if st.button("Run"):
        c.execute("SELECT name,resume,file_hash FROM candidates")
        data = c.fetchall()

        names=[d[0] for d in data]
        resumes=[d[1] for d in data]
        hashes=[d[2] for d in data]

        docs = resumes+[job]
        tfidf=TfidfVectorizer()
        mat=tfidf.fit_transform(docs)

        scores=cosine_similarity(mat[-1],mat[:-1])[0]

        df=pd.DataFrame({
            "Name":names,
            "Score":[round(s*100,2) for s in scores],
            "Hash":hashes,
            "Resume":resumes
        }).sort_values(by="Score",ascending=False)

        st.dataframe(df[["Name","Score"]])

        st.success(f"🏆 Best: {df.iloc[0]['Name']}")

        shortlist = st.slider("Shortlist top N",1,len(df),3)
        st.write("🎯 Shortlisted:", df.head(shortlist)["Name"].tolist())

        for i,row in df.iterrows():
            with st.expander(row["Name"]):

                st.write("🧠 Feedback:", feedback(row["Score"]))
                st.write("📊 Status:", detect_fake(row["Resume"]))
                st.write("🏷 Skills:", extract_skills(row["Resume"]))

                st.text_area("Resume Preview", row["Resume"][:800], key=f"p{i}")

                col1,col2 = st.columns(2)

                if col1.button("Hire", key=f"h{i}"):
                    c.execute("UPDATE candidates SET status='employed' WHERE file_hash=?",(row["Hash"],))
                    conn.commit()
                    st.rerun()

                if col2.button("Reject", key=f"r{i}"):
                    c.execute("UPDATE candidates SET status='rejected' WHERE file_hash=?",(row["Hash"],))
                    conn.commit()
                    st.rerun()

# ---------------- ANALYTICS ----------------
elif page=="Analytics":
    c.execute("SELECT status FROM candidates")
    data=c.fetchall()

    if data:
        df=pd.DataFrame(data,columns=["Status"])
        counts=df["Status"].value_counts()

        fig,ax=plt.subplots()
        counts.plot(kind="bar",ax=ax)
        st.pyplot(fig)

# ---------------- DATABASE ----------------
elif page=="Database":
    c.execute("SELECT name,status,file_hash FROM candidates")
    data=c.fetchall()

    df=pd.DataFrame(data,columns=["Name","Status","Hash"])
    st.dataframe(df[["Name","Status"]])

    st.subheader("Delete Candidate")

    if not df.empty:
        selected=st.selectbox("Select",df["Name"])
        h=df[df["Name"]==selected]["Hash"].values[0]

        if st.checkbox("Confirm"):
            if st.button("Delete"):
                c.execute("DELETE FROM candidates WHERE file_hash=?",(h,))
                conn.commit()
                st.success("Deleted")
                st.rerun()
