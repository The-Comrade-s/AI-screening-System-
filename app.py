import streamlit as st
import sqlite3
import pdfplumber
import pandas as pd
import hashlib
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI HR System", layout="wide")

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
.stButton>button {
    background-color: #4CDF50;
    color: white;
    border-radius: 6px;
    height: 3em;
    width: 100%;
    font-size: 20px;
}
.stSidebar {
    background-color: #F2F2F2;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#4CAF50;'>AI Resume Screening System</h1>", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("system.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT UNIQUE,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    name TEXT,
    resume TEXT,
    status TEXT,
    file_hash TEXT UNIQUE
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def get_file_hash(file):
    file_bytes = file.read()
    file.seek(0)
    return hashlib.md5(file_bytes).hexdigest()

def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def detect_fake(resume):
    if len(resume.split()) < 50:
        return "⚠️ Too short / suspicious"
    if "lorem" in resume.lower():
        return "⚠️ Fake-like content detected"
    return "✅ Genuine"

def hr_feedback(score):
    if score > 75:
        return "Excellent candidate — Strong match for role."
    elif score > 50:
        return "Good candidate — suitable for interview."
    elif score > 30:
        return "Average match — consider with caution."
    else:
        return "Weak candidate — not recommended."

# ---------------- SESSION ----------------
if "login" not in st.session_state:
    st.session_state.login = False

# ---------------- AUTH ----------------
if not st.session_state.login:
    st.markdown("## HR Access Portal")

    auth = st.radio("Select Option", ["Login", "Register"])

    if auth == "Register":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Register"):
            try:
                c.execute("INSERT INTO users VALUES (?,?)", (u, p))
                conn.commit()
                st.success("Account created!")
            except:
                st.error("Username already exists")

    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            if c.fetchone():
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- SIDEBAR ----------------
page = st.sidebar.radio("Navigation", ["Dashboard", "Upload", "Screening", "Analytics", "Database"])

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    c.execute("SELECT COUNT(*) FROM candidates")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM candidates WHERE status='employed'")
    hired = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM candidates WHERE status='rejected'")
    rejected = c.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Candidates", total)
    col2.metric("Hired", hired)
    col3.metric("Rejected", rejected)

# ---------------- UPLOAD ----------------
elif page == "Upload":
    st.subheader("Upload Resume")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        file_hash = get_file_hash(file)
        text = extract_text(file)

        c.execute("SELECT * FROM candidates WHERE file_hash=?", (file_hash,))
        exists = c.fetchone()

        if exists:
            st.error("Duplicate resume detected ❌")
        else:
            c.execute(
                "INSERT INTO candidates VALUES (?,?,?,?)",
                (file.name, text, "pending", file_hash)
            )
            conn.commit()
            st.success("Uploaded successfully ✔")
            st.rerun()

# ---------------- SCREENING ----------------
elif page == "Screening":
    st.subheader("AI Screening System")

    job_desc = st.text_area("Enter Job Description")

    if st.button("Run Screening"):
        c.execute("SELECT name, resume, file_hash FROM candidates")
        data = c.fetchall()

        if not data:
            st.warning("No resumes found")
        else:
            names = [d[0] for d in data]
            resumes = [d[1] for d in data]
            hashes = [d[2] for d in data]

            docs = resumes + [job_desc]

            tfidf = TfidfVectorizer()
            matrix = tfidf.fit_transform(docs)

            scores = cosine_similarity(matrix[-1], matrix[:-1])[0]

            results = []
            for i in range(len(names)):
                results.append({
                    "Name": names[i],
                    "Score": round(scores[i]*100, 2),
                    "Hash": hashes[i],
                    "Status": detect_fake(resumes[i]),
                    "Feedback": hr_feedback(scores[i]*100)
                })

            df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

            st.dataframe(df[["Name", "Score", "Status"]])

            best = df.iloc[0]
            st.success(f"🏆 Best Candidate: {best['Name']} ({best['Score']}%)")

            for i, row in df.iterrows():
                with st.expander(f"{row['Name']} - {row['Score']}%"):

                    st.info(row["Feedback"])

                    col1, col2 = st.columns(2)

                    # ---------------- FIXED HIRE ----------------
                    if col1.button(f"Hire {row['Name']}", key=f"h{i}"):

                        c.execute("""
                            UPDATE candidates
                            SET status='employed'
                            WHERE file_hash=?
                        """, (row["Hash"],))

                        conn.commit()
                        st.success("Hired ✔")
                        st.rerun()

                    # ---------------- FIXED REJECT ----------------
                    if col2.button(f"Reject {row['Name']}", key=f"r{i}"):

                        c.execute("""
                            UPDATE candidates
                            SET status='rejected'
                            WHERE file_hash=?
                        """, (row["Hash"],))

                        conn.commit()
                        st.error("Rejected ❌")
                        st.rerun()

# ---------------- ANALYTICS ----------------
elif page == "Analytics":
    st.subheader("Hiring Analytics")

    c.execute("SELECT status FROM candidates")
    data = c.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["Status"])
        counts = df["Status"].value_counts()

        fig, ax = plt.subplots()
        counts.plot(kind="bar", ax=ax)
        ax.set_title("Candidate Status Distribution")

        st.pyplot(fig)
    else:
        st.warning("No data available")

# ---------------- DATABASE ----------------
elif page == "Database":
    st.subheader("Candidate Database")

    c.execute("SELECT name, status FROM candidates")
    data = c.fetchall()

    df = pd.DataFrame(data, columns=["Name", "Status"])

    st.dataframe(df)
