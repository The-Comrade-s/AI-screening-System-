import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import re
from datetime import date

# Optional imports with graceful fallback
try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_ML = True
except ImportError:
    HAS_ML = False

# ─── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="MY AI – HR Recruitment",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0D1117 !important;
    color: #E6EDF3 !important;
}
.stApp { background-color: #0D1117 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 2.5rem !important; max-width: 1200px; }

section[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right: 1px solid #21262D !important;
}
section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background-color: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 10px !important;
    color: #E6EDF3 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00D4AA !important;
    box-shadow: 0 0 0 2px #00D4AA22 !important;
}

.stButton > button {
    background-color: #00D4AA !important;
    color: #0D1117 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 22px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background-color: #00FFCC !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 20px #00D4AA44 !important;
}
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid #21262D !important;
    color: #8B949E !important;
}

[data-testid="stMetric"] {
    background: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #00D4AA !important;
}
[data-testid="stMetricLabel"] { font-size: 13px !important; color: #8B949E !important; }

.stTabs [data-baseweb="tab-list"] {
    background: #161B22 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 9px !important;
    color: #8B949E !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] { background: #00D4AA !important; color: #0D1117 !important; }

.stProgress > div > div > div { background-color: #00D4AA !important; border-radius: 4px !important; }
.stProgress > div > div { background-color: #21262D !important; border-radius: 4px !important; }

.stSuccess { background: #0D2B1E !important; border-color: #2ECC71 !important; border-radius: 10px !important; }
.stError   { background: #2B0D17 !important; border-color: #FF4D6D !important; border-radius: 10px !important; }
.stWarning { background: #2B2200 !important; border-color: #FFB800 !important; border-radius: 10px !important; }
.stInfo    { background: #0D1B2B !important; border-color: #00D4AA !important;  border-radius: 10px !important; }

[data-testid="stFileUploader"] {
    background: #161B22 !important;
    border: 2px dashed #21262D !important;
    border-radius: 16px !important;
    padding: 20px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #00D4AA !important; }

.stDataFrame { border: 1px solid #21262D !important; border-radius: 16px !important; overflow: hidden !important; }
[data-testid="stDataFrame"] th {
    background: #0D1117 !important; color: #8B949E !important;
    font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.8px !important;
}
[data-testid="stDataFrame"] td { background: #161B22 !important; color: #E6EDF3 !important; border-color: #21262D !important; }

.streamlit-expanderHeader {
    background: #161B22 !important;
    border-radius: 10px !important;
    border: 1px solid #21262D !important;
    color: #E6EDF3 !important;
}
.streamlit-expanderContent {
    background: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 0 0 10px 10px !important;
}

hr { border-color: #21262D !important; }
h1,h2,h3,h4 { font-family: 'Syne', sans-serif !important; }
select option { background: #161B22; color: #E6EDF3; }

.hire-card {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# ─── Database ────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    conn = sqlite3.connect("system.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS candidates (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        role        TEXT,
        resume      TEXT,
        score       REAL DEFAULT 0,
        status      TEXT DEFAULT 'Reviewing',
        skills      TEXT,
        file_hash   TEXT UNIQUE,
        email       TEXT,
        notes       TEXT,
        date_added  TEXT
    )""")
    # Migrate old DB: add missing columns safely
    existing = [row[1] for row in cur.execute("PRAGMA table_info(candidates)").fetchall()]
    for col, typedef in [("role","TEXT"),("score","REAL DEFAULT 0"),("skills","TEXT"),
                          ("email","TEXT"),("notes","TEXT"),("date_added","TEXT")]:
        if col not in existing:
            cur.execute(f"ALTER TABLE candidates ADD COLUMN {col} {typedef}")
    conn.commit()
    return conn, cur

conn, cur = get_db()


# ─── Helpers ─────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_file_hash(file):
    b = file.read(); file.seek(0)
    return hashlib.md5(b).hexdigest()

def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "pdf":
        if not HAS_PDF:
            st.warning("pdfplumber not installed. Add it to requirements.txt")
            return ""
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text += p.extract_text() or ""
        return text
    elif ext == "docx":
        if not HAS_DOCX:
            st.warning("python-docx not installed. Add it to requirements.txt")
            return ""
        d = docx.Document(file)
        return "\n".join([p.text for p in d.paragraphs])
    elif ext in ["png","jpg","jpeg"]:
        if not HAS_OCR:
            st.warning("pytesseract/Pillow not installed.")
            return ""
        return pytesseract.image_to_string(Image.open(file))
    return ""

def ai_score(resume_text, job_description):
    """Real TF-IDF cosine similarity. Falls back to keyword density."""
    if not resume_text.strip():
        return 0.0
    if not HAS_ML or not job_description.strip():
        words = resume_text.lower().split()
        return float(min(100, len(set(words)) // 3))
    try:
        vec = TfidfVectorizer(stop_words="english")
        mat = vec.fit_transform([resume_text, job_description])
        score = cosine_similarity(mat[0], mat[1])[0][0]
        return round(score * 100, 1)
    except Exception:
        return 0.0

def detect_fake(text):
    if len(text.split()) < 50:
        return "⚠️ Suspicious — very short resume"
    if re.search(r"(lorem ipsum|test test|asdfgh)", text.lower()):
        return "⚠️ Suspicious — placeholder text detected"
    return "✅ Genuine"

def extract_skills(text):
    skill_list = [
        "python","java","javascript","typescript","react","vue","angular","flutter","dart",
        "sql","postgresql","mysql","mongodb","firebase","redis",
        "docker","kubernetes","aws","gcp","azure","linux","git",
        "machine learning","deep learning","tensorflow","pytorch","pandas","numpy",
        "fastapi","django","flask","node","express",
        "figma","photoshop","agile","scrum","jira",
        "communication","leadership","teamwork",
    ]
    return [k.title() for k in skill_list if k in text.lower()][:10]

def ai_feedback(score):
    if score >= 80: return "🏆 Excellent match. Strong candidate — recommend fast-tracking."
    if score >= 65: return "✅ Good match. Solid profile worth interviewing."
    if score >= 45: return "⚠️ Moderate match. May need further evaluation."
    return "❌ Weak match. Does not meet role requirements."

def status_decision(score):
    if score >= 80: return "Hired"
    if score >= 50: return "Reviewing"
    return "Rejected"

def score_color(s):
    if s >= 80: return "#2ECC71"
    if s >= 65: return "#FFB800"
    return "#FF4D6D"

def status_badge(status):
    cfg = {
        "Hired":     ("#0D2B1E","#2ECC71"),
        "Rejected":  ("#2B0D17","#FF4D6D"),
        "Reviewing": ("#2B2200","#FFB800"),
        "pending":   ("#2B2200","#FFB800"),
        "employed":  ("#0D2B1E","#2ECC71"),
        "rejected":  ("#2B0D17","#FF4D6D"),
    }
    bg, color = cfg.get(status, ("#2B2200","#FFB800"))
    label = {"pending":"Reviewing","employed":"Hired"}.get(status, status)
    return f'<span style="background:{bg};color:{color};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;">{label}</span>'


# ─── Session state ───────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""


# ─── Login ───────────────────────────────────────────────────────────
def login_page():
    st.markdown("""
    <div style="text-align:center;padding:40px 0 20px;">
        <div style="font-size:52px;margin-bottom:10px;">🚀</div>
        <h1 style="font-size:32px;font-weight:800;color:#E6EDF3;margin:0;">HireAI</h1>
        <p style="color:#8B949E;font-size:15px;margin-top:8px;">Intelligent HR Recruitment Platform</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        tab_in, tab_reg = st.tabs(["Sign In", "Register"])

        with tab_in:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            u = st.text_input("Username", placeholder="Enter username", key="li_u")
            p = st.text_input("Password", type="password", placeholder="••••••••", key="li_p")
            if st.button("Sign In →", key="btn_login", use_container_width=True):
                cur.execute("SELECT password FROM users WHERE username=?", (u,))
                row = cur.fetchone()
                # Support both hashed (new) and plain text (legacy) passwords
                if row and (row[0] == hash_pw(p) or row[0] == p):
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab_reg:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            nu  = st.text_input("Choose Username", placeholder="e.g. hr_admin", key="reg_u")
            np  = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_p")
            np2 = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="reg_p2")
            if st.button("Create Account →", key="btn_reg", use_container_width=True):
                if not nu or not np:
                    st.error("All fields are required.")
                elif np != np2:
                    st.error("Passwords do not match.")
                elif len(np) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        cur.execute("INSERT INTO users VALUES (?,?)", (nu, hash_pw(np)))
                        conn.commit()
                        st.success(f"Account created! Sign in as **{nu}**.")
                    except sqlite3.IntegrityError:
                        st.error("Username already taken.")


# ─── Sidebar ─────────────────────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:10px 0 24px;border-bottom:1px solid #21262D;margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:28px;">🚀</span>
                <span style="font-family:'Syne',sans-serif;font-weight:800;font-size:20px;color:#00D4AA;">HireAI</span>
            </div>
            <p style="color:#8B949E;font-size:12px;margin:6px 0 0 38px;">Recruitment Platform</p>
        </div>
        """, unsafe_allow_html=True)

        page = st.radio("Menu", ["⚡ Dashboard","📤 Upload","🔍 Screening","📊 Analytics","🗄️ Database"], label_visibility="collapsed")

        st.markdown("<hr>", unsafe_allow_html=True)
        uname = st.session_state.username
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="width:34px;height:34px;border-radius:50%;background:#00D4AA;display:flex;align-items:center;justify-content:center;font-weight:700;color:#0D1117;font-size:15px;">{uname[0].upper()}</div>
            <div>
                <div style="font-size:14px;font-weight:500;">{uname}</div>
                <div style="font-size:11px;color:#484F58;">HR Manager</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.rerun()

    return page.split(" ", 1)[1].strip()


# ─── Dashboard ────────────────────────────────────────────────────────
def dashboard():
    st.markdown("<h2 style='margin:0 0 4px'>⚡ Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8B949E;margin-bottom:28px;'>Welcome back! Here's your recruitment overview.</p>", unsafe_allow_html=True)

    total     = cur.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    hired     = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Hired','employed')").fetchone()[0]
    rejected  = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Rejected','rejected')").fetchone()[0]
    reviewing = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Reviewing','pending')").fetchone()[0]
    avg_score = round(cur.execute("SELECT AVG(score) FROM candidates").fetchone()[0] or 0)

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("👥 Total", total)
    c2.metric("✅ Hired", hired)
    c3.metric("❌ Rejected", rejected)
    c4.metric("⏳ Reviewing", reviewing)
    c5.metric("🎯 Avg Score", f"{avg_score}%")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1.4, 1])

    with col_a:
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 16px;color:#E6EDF3'>📅 Monthly Applications</h4>", unsafe_allow_html=True)
        monthly = pd.DataFrame({
            "Month":   ["Jan","Feb","Mar","Apr","May","Jun"],
            "Applied": [12,18,24,15,30,22],
            "Hired":   [4, 7, 9, 5, 11, 8],
            "Rejected":[5, 6, 8, 7, 10, 7],
        })
        st.bar_chart(monthly.set_index("Month"), color=["#00D4AA","#2ECC71","#FF4D6D"], height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 16px;color:#E6EDF3'>🎯 Status Breakdown</h4>", unsafe_allow_html=True)
        if total > 0:
            bd = pd.DataFrame({"Status":["Hired","Rejected","Reviewing"],"Count":[hired,rejected,reviewing]})
            st.bar_chart(bd.set_index("Status"), color=["#00D4AA"], height=150)
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;">
            <span style="font-size:13px;">🟢 Hired: <b style='color:#2ECC71'>{hired}</b></span>
            <span style="font-size:13px;">🔴 Rejected: <b style='color:#FF4D6D'>{rejected}</b></span>
            <span style="font-size:13px;">🟡 Reviewing: <b style='color:#FFB800'>{reviewing}</b></span>
        </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='hire-card'><h4 style='margin:0 0 16px;'>🕐 Recent Candidates</h4>", unsafe_allow_html=True)
    rows = cur.execute("SELECT name,role,score,status,date_added FROM candidates ORDER BY id DESC LIMIT 6").fetchall()
    if rows:
        for name, role, score, status, dt in rows:
            sc = score or 0
            r1,r2,r3,r4 = st.columns([2,2,1,1])
            r1.markdown(f"**{name}**")
            r2.markdown(f"<span style='color:#8B949E;font-size:13px'>{role or '—'}</span>", unsafe_allow_html=True)
            r3.markdown(f"<span style='color:{score_color(sc)};font-weight:700;font-size:16px'>{sc}%</span>", unsafe_allow_html=True)
            r4.markdown(status_badge(status), unsafe_allow_html=True)
            st.markdown("<hr style='margin:6px 0;border-color:#21262D'>", unsafe_allow_html=True)
    else:
        st.info("No candidates yet. Upload resumes to get started.")
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Upload ───────────────────────────────────────────────────────────
def upload_page():
    st.markdown("<h2 style='margin:0 0 4px'>📤 Upload Resume</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8B949E;margin-bottom:28px;'>Real text extraction from PDF/DOCX/Image + TF-IDF AI scoring.</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        uploaded   = st.file_uploader("Upload Resume", type=["pdf","docx","png","jpg","jpeg"])
        cand_name  = st.text_input("Candidate Full Name *", placeholder="e.g. Amara Okafor")
        cand_role  = st.text_input("Applied Role *", placeholder="e.g. Frontend Engineer")
        cand_email = st.text_input("Email (optional)", placeholder="candidate@email.com")

    with col2:
        jd = st.text_area("Job Description (for AI scoring)", placeholder="Paste job description here for accurate TF-IDF match score…", height=180)
        if st.button("🔍 Run AI Screening", use_container_width=True):
            if not uploaded:
                st.error("Please upload a resume file.")
            elif not cand_name or not cand_role:
                st.error("Candidate name and role are required.")
            else:
                with st.spinner("⚙️ Extracting text and running TF-IDF analysis…"):
                    fhash = get_file_hash(uploaded)
                    cur.execute("SELECT id FROM candidates WHERE file_hash=?", (fhash,))
                    if cur.fetchone():
                        st.error("❌ Duplicate resume — this file is already in the database.")
                    else:
                        text   = extract_text(uploaded)
                        if not text.strip():
                            st.error("Could not extract text. Try PDF or DOCX format.")
                        else:
                            score   = ai_score(text, jd)
                            skills  = extract_skills(text)
                            fake    = detect_fake(text)
                            status  = status_decision(score)
                            verdict = ai_feedback(score)
                            st.session_state["pending"] = {
                                "name":      cand_name,
                                "role":      cand_role,
                                "email":     cand_email or f"{cand_name.lower().replace(' ','.')}@mail.com",
                                "resume":    text,
                                "score":     score,
                                "status":    status,
                                "skills":    ", ".join(skills) if skills else "Not detected",
                                "file_hash": fhash,
                                "date_added":str(date.today()),
                                "fake":      fake,
                                "verdict":   verdict,
                            }

    if "pending" in st.session_state:
        p  = st.session_state["pending"]
        sc = p["score"]
        cl = score_color(sc)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='hire-card' style='border-color:{cl}55;'>
            <div style='display:flex;align-items:center;gap:16px;margin-bottom:16px;'>
                <div style='width:56px;height:56px;border-radius:50%;border:3px solid {cl};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:17px;color:{cl}'>{sc}%</div>
                <div>
                    <div style='font-family:Syne,sans-serif;font-weight:700;font-size:18px'>{p['name']}</div>
                    <div style='color:#8B949E;font-size:13px'>{p['role']} • {p['email']}</div>
                </div>
                {status_badge(p['status'])}
            </div>
            <p style='color:#8B949E;font-size:14px;margin-bottom:8px'>{p['verdict']}</p>
            <p style='color:#8B949E;font-size:13px;margin-bottom:10px'>Authenticity: <b style="color:{cl}">{p['fake']}</b></p>
            <div style='display:flex;gap:8px;flex-wrap:wrap;'>
                {''.join(f"<span style='background:#00D4AA22;color:#00D4AA;font-size:11px;padding:3px 12px;border-radius:20px'>{s.strip()}</span>" for s in p['skills'].split(','))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📄 Extracted Resume Text Preview"):
            st.text_area("", p["resume"][:1500], height=180, label_visibility="collapsed")

        sa, sb = st.columns([1, 3])
        with sa:
            if st.button("✅ Save to Database", key="save_p"):
                cur.execute("""INSERT INTO candidates
                    (name,role,resume,score,status,skills,file_hash,email,notes,date_added)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (p["name"],p["role"],p["resume"],p["score"],p["status"],
                     p["skills"],p["file_hash"],p["email"],"",p["date_added"]))
                conn.commit()
                del st.session_state["pending"]
                st.success("Candidate saved successfully!")
                st.rerun()
        with sb:
            if st.button("Discard", key="discard_p"):
                del st.session_state["pending"]
                st.rerun()


# ─── Screening ────────────────────────────────────────────────────────
def screening_page():
    st.markdown("<h2 style='margin:0 0 4px'>🔍 AI Screening</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8B949E;margin-bottom:24px;'>Re-score all candidates against a job description using TF-IDF cosine similarity.</p>", unsafe_allow_html=True)

    jd = st.text_area("Paste Job Description", placeholder="Enter job description to rank all candidates…", height=140)

    if st.button("🚀 Run AI Screening on All Candidates", use_container_width=False):
        rows = cur.execute("SELECT id,name,resume,file_hash FROM candidates").fetchall()
        if not rows:
            st.warning("No candidates in database. Upload resumes first.")
        elif not jd.strip():
            st.warning("Please enter a job description.")
        else:
            with st.spinner("Running TF-IDF analysis on all resumes…"):
                results = []
                for rid, name, resume, fhash in rows:
                    score = ai_score(resume or "", jd)
                    new_status = status_decision(score)
                    cur.execute("UPDATE candidates SET score=?, status=? WHERE id=?", (score, new_status, rid))
                    results.append({"id":rid,"name":name,"score":score,"status":new_status,"hash":fhash,"resume":resume or ""})
                conn.commit()
                st.session_state["screen_results"] = sorted(results, key=lambda x: x["score"], reverse=True)

    if "screen_results" in st.session_state:
        results = st.session_state["screen_results"]
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.success(f"🏆 Best match: **{results[0]['name']}** — {results[0]['score']}%")

        n = st.slider("Shortlist top N candidates", 1, max(1,len(results)), min(3,len(results)))
        st.info(f"🎯 Shortlisted: {', '.join(r['name'] for r in results[:n])}")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for r in results:
            sc  = r["score"]
            cl  = score_color(sc)
            with st.expander(f"{r['name']}  —  {sc}%", expanded=False):
                c1, c2 = st.columns(2)
                c1.markdown(f"**Match Score:** <span style='color:{cl};font-size:20px;font-weight:800'>{sc}%</span>", unsafe_allow_html=True)
                c2.markdown(f"**AI Feedback:** {ai_feedback(sc)}")
                st.markdown(f"**Authenticity:** {detect_fake(r['resume'])}")
                skills = extract_skills(r["resume"])
                if skills:
                    st.markdown("**Skills Detected:** " + " ".join(f"`{s}`" for s in skills))
                st.text_area("Resume Preview", r["resume"][:800], height=120, key=f"prev_{r['id']}")
                h_col, r_col = st.columns(2)
                if h_col.button("✅ Hire", key=f"hire_{r['id']}"):
                    cur.execute("UPDATE candidates SET status='Hired' WHERE id=?", (r["id"],))
                    conn.commit(); st.success(f"{r['name']} marked as Hired!"); st.rerun()
                if r_col.button("❌ Reject", key=f"rej_{r['id']}"):
                    cur.execute("UPDATE candidates SET status='Rejected' WHERE id=?", (r["id"],))
                    conn.commit(); st.error(f"{r['name']} rejected."); st.rerun()

    # Manual queue
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin:16px 0 8px;'>📋 Manual Review Queue</h4>", unsafe_allow_html=True)
    queue = cur.execute("SELECT id,name,role,score,status FROM candidates WHERE status IN ('Reviewing','pending')").fetchall()
    if not queue:
        st.info("No candidates pending manual review.")
    else:
        for rid, name, role, score, status in queue:
            sc = score or 0
            cl = score_color(sc)
            c1,c2,c3,c4,c5 = st.columns([2,2,1,1,1])
            c1.markdown(f"**{name}**")
            c2.markdown(f"<span style='color:#8B949E;font-size:13px'>{role or '—'}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color:{cl};font-weight:700'>{sc}%</span>", unsafe_allow_html=True)
            c4.markdown(status_badge(status), unsafe_allow_html=True)
            with c5:
                if st.button("✅", key=f"qh_{rid}", help="Hire"):
                    cur.execute("UPDATE candidates SET status='Hired' WHERE id=?", (rid,))
                    conn.commit(); st.rerun()
                if st.button("❌", key=f"qr_{rid}", help="Reject"):
                    cur.execute("UPDATE candidates SET status='Rejected' WHERE id=?", (rid,))
                    conn.commit(); st.rerun()
            st.markdown("<hr style='margin:4px 0;border-color:#21262D'>", unsafe_allow_html=True)


# ─── Analytics ────────────────────────────────────────────────────────
def analytics_page():
    st.markdown("<h2 style='margin:0 0 4px'>📊 Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#8B949E;margin-bottom:28px;'>Live insights from your SQLite recruitment database.</p>", unsafe_allow_html=True)

    total     = cur.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    hired     = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Hired','employed')").fetchone()[0]
    rejected  = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Rejected','rejected')").fetchone()[0]
    reviewing = cur.execute("SELECT COUNT(*) FROM candidates WHERE status IN ('Reviewing','pending')").fetchone()[0]
    avg_score = round(cur.execute("SELECT AVG(score) FROM candidates").fetchone()[0] or 0)
    hire_rate = round((hired/total)*100) if total else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📈 Hire Rate",   f"{hire_rate}%")
    c2.metric("🎯 Avg Score",   avg_score)
    c3.metric("⏳ In Pipeline", reviewing)
    c4.metric("📉 Rejected",    rejected)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 14px'>📅 Monthly Trend</h4>", unsafe_allow_html=True)
        monthly = pd.DataFrame({
            "Month":   ["Jan","Feb","Mar","Apr","May","Jun"],
            "Applied": [12,18,24,15,30,22],
            "Hired":   [4, 7, 9, 5, 11, 8],
            "Rejected":[5, 6, 8, 7, 10, 7],
        })
        st.line_chart(monthly.set_index("Month"), color=["#00D4AA","#2ECC71","#FF4D6D"], height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 14px'>🏆 Top Performers</h4>", unsafe_allow_html=True)
        top = cur.execute("SELECT name,role,score FROM candidates ORDER BY score DESC LIMIT 5").fetchall()
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
        if top:
            for i,(name,role,sc) in enumerate(top):
                sc = sc or 0
                cl = score_color(sc)
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #21262D'>
                    <span style='font-size:16px'>{medals[i]}</span>
                    <div style='flex:1'>
                        <div style='font-size:13px;font-weight:600'>{name}</div>
                        <div style='font-size:11px;color:#8B949E'>{role or "—"}</div>
                    </div>
                    <span style='background:#00D4AA22;color:{cl};padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700'>{sc}%</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No data yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Live role distribution
    role_rows = cur.execute("SELECT role, COUNT(*) FROM candidates WHERE role IS NOT NULL GROUP BY role ORDER BY COUNT(*) DESC").fetchall()
    if role_rows:
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 14px'>📋 Applications by Role</h4>", unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame(role_rows, columns=["Role","Count"]).set_index("Role"), color=["#00D4AA"], height=200)
        st.markdown("</div>", unsafe_allow_html=True)

    # Live score distribution
    score_rows = cur.execute("SELECT name, score FROM candidates WHERE score IS NOT NULL ORDER BY score DESC").fetchall()
    if score_rows:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='hire-card'><h4 style='margin:0 0 14px'>🎯 Candidate Score Distribution</h4>", unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame(score_rows, columns=["Candidate","Score"]).set_index("Candidate"), color=["#7B61FF"], height=200)
        st.markdown("</div>", unsafe_allow_html=True)


# ─── Database ─────────────────────────────────────────────────────────
def database_page():
    st.markdown("<h2 style='margin:0 0 4px'>🗄️ Candidate Database</h2>", unsafe_allow_html=True)
    total = cur.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    st.markdown(f"<p style='color:#8B949E;margin-bottom:24px;'>{total} candidates in database.</p>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([2,1,1])
    with c1:
        search = st.text_input("🔍 Search", placeholder="Name or role…", label_visibility="collapsed")
    with c2:
        sf = st.selectbox("Status", ["All","Hired","Reviewing","Rejected"], label_visibility="collapsed")
    with c3:
        sort = st.selectbox("Sort", ["Newest","Score ↓","Name A-Z"], label_visibility="collapsed")

    query = "SELECT id,name,role,score,status,skills,email,date_added,notes FROM candidates WHERE 1=1"
    params = []
    if sf == "Hired":      query += " AND status IN ('Hired','employed')"
    elif sf == "Rejected": query += " AND status IN ('Rejected','rejected')"
    elif sf == "Reviewing":query += " AND status IN ('Reviewing','pending')"
    if search:
        query += " AND (name LIKE ? OR role LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if sort == "Score ↓":    query += " ORDER BY score DESC"
    elif sort == "Name A-Z": query += " ORDER BY name ASC"
    else:                    query += " ORDER BY id DESC"

    rows = cur.execute(query, params).fetchall()

    if not rows:
        st.info("No candidates match your filter.")
        return

    st.markdown("""
    <div style='display:grid;grid-template-columns:2fr 2fr 80px 110px 100px 120px;padding:10px 16px;
    background:#0D1117;border-radius:12px 12px 0 0;border:1px solid #21262D;margin-top:16px;'>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Name</span>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Role</span>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Score</span>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Status</span>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Date</span>
        <span style='font-size:11px;color:#484F58;font-weight:600;text-transform:uppercase;letter-spacing:.8px'>Actions</span>
    </div>
    """, unsafe_allow_html=True)

    for row in rows:
        rid, name, role, score, status, skills, email, dt, notes = row
        sc = score or 0
        cl = score_color(sc)
        r1,r2,r3,r4,r5,r6 = st.columns([2,2,0.8,1.1,1,1.2])
        r1.markdown(f"**{name}**<br><span style='color:#484F58;font-size:11px'>{email or '—'}</span>", unsafe_allow_html=True)
        r2.markdown(f"<span style='color:#8B949E;font-size:13px'>{role or '—'}</span>", unsafe_allow_html=True)
        r3.markdown(f"<span style='color:{cl};font-weight:700;font-size:16px'>{sc}%</span>", unsafe_allow_html=True)
        r4.markdown(status_badge(status), unsafe_allow_html=True)
        r5.markdown(f"<span style='color:#8B949E;font-size:12px'>{dt or '—'}</span>", unsafe_allow_html=True)
        with r6:
            if st.button("✏️", key=f"ed_{rid}", help="Edit"):
                st.session_state[f"edit_{rid}"] = True
            if st.button("🗑️", key=f"dl_{rid}", help="Delete"):
                st.session_state[f"del_{rid}"] = True

        if st.session_state.get(f"edit_{rid}"):
            with st.expander(f"✏️ Edit — {name}", expanded=True):
                ns = st.selectbox("Status", ["Hired","Reviewing","Rejected"],
                    index=["Hired","Reviewing","Rejected"].index(
                        "Hired" if status in ("Hired","employed") else
                        "Rejected" if status in ("Rejected","rejected") else "Reviewing"),
                    key=f"ns_{rid}")
                nn = st.text_input("Notes", value=notes or "", key=f"nn_{rid}")
                s1, s2 = st.columns(2)
                if s1.button("💾 Save", key=f"sv_{rid}"):
                    cur.execute("UPDATE candidates SET status=?, notes=? WHERE id=?", (ns, nn, rid))
                    conn.commit(); del st.session_state[f"edit_{rid}"]
                    st.success("Updated!"); st.rerun()
                if s2.button("Cancel", key=f"ce_{rid}"):
                    del st.session_state[f"edit_{rid}"]; st.rerun()

        if st.session_state.get(f"del_{rid}"):
            with st.expander(f"⚠️ Delete {name}?", expanded=True):
                st.warning("This action cannot be undone.")
                d1, d2 = st.columns(2)
                if d1.button("🗑️ Confirm Delete", key=f"cd_{rid}"):
                    cur.execute("DELETE FROM candidates WHERE id=?", (rid,))
                    conn.commit(); del st.session_state[f"del_{rid}"]
                    st.success("Deleted."); st.rerun()
                if d2.button("Cancel", key=f"cd2_{rid}"):
                    del st.session_state[f"del_{rid}"]; st.rerun()

        st.markdown("<hr style='margin:4px 0;border-color:#21262D'>", unsafe_allow_html=True)

    # Export
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    exp = cur.execute("SELECT name,role,score,status,skills,email,date_added,notes FROM candidates").fetchall()
    df_exp = pd.DataFrame(exp, columns=["Name","Role","Score","Status","Skills","Email","Date","Notes"])
    st.download_button("⬇️ Export All to CSV", df_exp.to_csv(index=False).encode("utf-8"), "candidates.csv", "text/csv")


# ─── Main ─────────────────────────────────────────────────────────────
def main():
    if not st.session_state.authenticated:
        login_page()
        return
    page = sidebar()
    if page == "Dashboard":  dashboard()
    elif page == "Upload":   upload_page()
    elif page == "Screening":screening_page()
    elif page == "Analytics":analytics_page()
    elif page == "Database": database_page()

main()
