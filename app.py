import streamlit as st
import sqlite3
import pdfplumber
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
    status TEXT
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def extract_text(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def generate_reason(resume, job_desc):
    resume_words = set(resume.lower().split())
    job_words = set(job_desc.lower().split())

    matched = resume_words & job_words
    missing = job_words - resume_words

    return f"""
✔ Matched skills: {', '.join(list(matched)[:5])}
❌ Missing skills: {', '.join(list(missing)[:5])}
"""

def detect_fake(resume):
    if len(resume.split()) < 50:
        return "⚠️ Too short (Possible fake)"
    if "lorem" in resume.lower():
        return "⚠️ Fake-like content detected"
    return "✅ Genuine"

# ---------------- SESSION ----------------
if "login" not in st.session_state:
    st.session_state.login = False

# ---------------- AUTH ----------------
if not st.session_state.login:
    st.title("HR AI System")

    auth = st.radio("Choose Action", ["Login", "Register"])

    # REGISTER
    if auth == "Register":
        st.subheader("Create Account")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            if new_user and new_pass:
                try:
                    c.execute("INSERT INTO users VALUES (?,?)", (new_user, new_pass))
                    conn.commit()
                    st.success("Account created! Now login.")
                except:
                    st.error("Username already exists")
            else:
                st.warning("Fill all fields")

    # LOGIN
    else:
        st.subheader("Login")

        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
            if c.fetchone():
                st.session_state.login = True
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("", ["Dashboard", "Upload Resume", "Screening", "Database"])

# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    st.title("Dashboard")

    conn.commit()
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
elif page == "Upload Resume":
    st.title("Upload Resume")

    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        text = extract_text(file)
        c.execute("INSERT INTO candidates VALUES (?,?,?)", (file.name, text, "pending"))
        conn.commit()
        st.success("Uploaded successfully!")
        st.rerun()

# ---------------- SCREENING ----------------
elif page == "Screening":
    st.title("AI Screening System")

    job_desc = st.text_area("Enter Job Description")

    if st.button("Run Screening"):
        c.execute("SELECT name, resume FROM candidates")
        data = c.fetchall()

        if not data:
            st.warning("No resumes uploaded")
        else:
            names = [d[0] for d in data]
            resumes = [d[1] for d in data]

            docs = resumes + [job_desc]

            tfidf = TfidfVectorizer()
            matrix = tfidf.fit_transform(docs)

            scores = cosine_similarity(matrix[-1], matrix[:-1])[0]

            results = []
            for i in range(len(names)):
                results.append({
                    "Name": names[i],
                    "Score": round(scores[i]*100,2),
                    "Resume": resumes[i],
                    "Reason": generate_reason(resumes[i], job_desc),
                    "Status": detect_fake(resumes[i])
                })

            df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

            st.dataframe(df[["Name","Score","Status"]])

            best = df.iloc[0]
            st.success(f"🏆 Best Candidate: {best['Name']} ({best['Score']}%)")

            for i, row in df.iterrows():
                with st.expander(f"{row['Name']} - {row['Score']}%"):

                    st.write(row["Reason"])
                    st.write(row["Status"])

                    col1, col2 = st.columns(2)

                    if col1.button(f"Hire {row['Name']}", key=f"h{i}"):
                        c.execute("UPDATE candidates SET status='employed' WHERE name=?", (row["Name"],))
                        conn.commit()
                        st.success("Hired successfully")
                        st.rerun()

                    if col2.button(f"Reject {row['Name']}", key=f"r{i}"):
                        c.execute("UPDATE candidates SET status='rejected' WHERE name=?", (row["Name"],))
                        conn.commit()
                        st.warning("Rejected successfully")
                        st.rerun()

# ---------------- DATABASE ----------------
elif page == "Database":
    st.title("Candidate Database")

    search = st.text_input("Search candidate")

    conn.commit()
    c.execute("SELECT * FROM candidates")
    data = c.fetchall()

    df = pd.DataFrame(data, columns=["Name","Resume","Status"])

    if search:
        df = df[df["Name"].str.contains(search, case=False)]

    st.dataframe(df)
