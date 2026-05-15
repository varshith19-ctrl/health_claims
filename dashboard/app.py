"""
Streamlit Dashboard.
Claim submission form → API → Conditional results display.
"""
import streamlit as st
import requests
import json
import os

st.set_page_config(
    page_title="ClaimShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp {
        background-color: #ffffff;
        color: #1d1d1f;
    }

    .main .block-container {
        max-width: 880px;
        padding: 2rem 1rem;
    }

    h1, h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1d1d1f;
        -webkit-text-fill-color: #1d1d1f;
        text-align: center;
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #86868b;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .card {
        background: #f5f5f7;
        border-radius: 18px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
    }
    .card-white {
        background: #ffffff;
        border: 1px solid #e8e8ed;
        border-radius: 18px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #ffffff !important;
        border: 1px solid #d2d2d7 !important;
        border-radius: 12px !important;
        color: #1d1d1f !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #0071e3 !important;
        box-shadow: 0 0 0 3px rgba(0,113,227,0.15) !important;
    }

    label { color: #6e6e73 !important; font-weight: 500 !important; font-size: 0.85rem !important; }

    .stButton > button {
        background: #0071e3 !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: #0077ED !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,113,227,0.3) !important;
    }

    .badge-denied { background: #ff3b30; color: white; padding: 5px 16px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
    .badge-accepted { background: #34c759; color: white; padding: 5px 16px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }
    .badge-medium { background: #ff9500; color: white; padding: 5px 16px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; display: inline-block; }

    .metric-box { text-align: center; padding: 1.25rem 0; }
    .metric-value { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.02em; }
    .metric-label { font-size: 0.8rem; color: #86868b; margin-top: 0.2rem; font-weight: 500; }

    .feature-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.65rem 1rem; margin-bottom: 0.4rem;
        background: #f5f5f7; border-radius: 10px;
    }
    .feature-row.alert {
        background: #fff5f5; border-left: 3px solid #ff3b30;
    }
    .feature-name { font-size: 0.88rem; color: #1d1d1f; }
    .feature-pct { font-size: 0.88rem; font-weight: 600; color: #1d1d1f; }

    .rec-item {
        background: #f0f5ff;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid #0071e3;
        font-size: 0.88rem;
        color: #1d1d1f;
    }

    .section-divider {
        height: 1px;
        background: #e8e8ed;
        margin: 1.5rem 0;
    }

    .accepted-banner {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border-radius: 18px;
        padding: 2.5rem;
        text-align: center;
        margin: 1rem 0;
        border: 1px solid #c8e6c9;
    }
    .accepted-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .accepted-title { font-size: 1.5rem; font-weight: 700; color: #2e7d32; }
    .accepted-sub { font-size: 0.95rem; color: #558b2f; margin-top: 0.3rem; }

    hr { border-color: #e8e8ed !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] { color: #1d1d1f !important; }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("API_URL", "http://localhost:8000/api")


def render_header():
    st.markdown('<div class="hero-title">ClaimShield AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">AI-Powered Claim Denial Prevention & Remediation</div>', unsafe_allow_html=True)


def render_form():
    st.markdown("### 📋 Submit a Claim for Analysis")
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        claim_id = st.text_input("Claim ID", placeholder="e.g. C1001")
        provider_id = st.selectbox("Provider ID", [
            "", "PR100", "PR101", "PR102", "PR103", "PR104", "PR105",
            "PR106", "PR107", "PR108", "PR109", "PR110", "PR111",
            "PR112", "PR113", "PR114", "PR115", "PR116", "PR117",
            "PR118", "PR119", "PR120",
        ])
        diagnosis_code = st.selectbox("Diagnosis Code", ["", "D10", "D20", "D30", "D40", "D50", "D60"])
    with col2:
        patient_id = st.text_input("Patient ID", placeholder="e.g. P001")
        procedure_code = st.selectbox("Procedure Code", ["", "PROC1", "PROC2", "PROC3", "PROC4", "PROC5", "PROC6"])
        billed_amount = st.number_input("Billed Amount ($)", min_value=0.0, value=15000.0, step=100.0)

    submitted = st.button("🔍  Analyze Claim Risk", use_container_width=True)
    return submitted, {
        "claim_id": claim_id,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "diagnosis_code": diagnosis_code,
        "procedure_code": procedure_code,
        "billed_amount": billed_amount,
    }


def render_results(data: dict):
    prediction = data["prediction"]
    risk = data["risk"]
    score = data["score"]

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    if prediction == "ACCEPTED":
        st.markdown(f"""
        <div class="accepted-banner">
            <div class="accepted-icon">✅</div>
            <div class="accepted-title">Claim Accepted</div>
            <div class="accepted-sub">Denial probability: {score:.0%} — This claim is within normal parameters.</div>
        </div>
        """, unsafe_allow_html=True)
        render_architecture_graph(data)
        return

    # DENIED / HIGH / MEDIUM path — show full analysis
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        score_color = "#ff3b30" if risk == "HIGH" else "#ff9500" if risk == "MEDIUM" else "#34c759"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color:{score_color}">{score:.0%}</div>
            <div class="metric-label">Denial Probability</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        badge = "badge-denied" if risk == "HIGH" else "badge-medium" if risk == "MEDIUM" else "badge-accepted"
        st.markdown(f"""
        <div class="metric-box">
            <div style="margin-top:0.5rem"><span class="{badge}">{risk} RISK</span></div>
            <div class="metric-label" style="margin-top:0.75rem">Risk Level</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="font-size:1.4rem;color:#ff3b30">DENIED</div>
            <div class="metric-label">Prediction</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Top 2 denial factors
    st.markdown("### 🎯 Top Factors Contributing to Denial")
    for feat_info in data.get("top_2_features", []):
        st.markdown(f"""
        <div class="feature-row alert">
            <span class="feature-name">⚠️ {feat_info['feature']}</span>
            <span class="feature-pct">{feat_info['percentage']}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # All feature contributions
    st.markdown("### 📊 All Feature Contributions")
    contributions = data.get("feature_contributions", {})
    sorted_contribs = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    for name, pct in sorted_contribs:
        st.markdown(f"""
        <div class="feature-row">
            <span class="feature-name">{name}</span>
            <span class="feature-pct">{pct}%</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # Policy explanation
    st.markdown("### 📜 Policy-Based Explanation")
    st.markdown(f'<div class="card">{data.get("policy_explanation", "N/A")}</div>', unsafe_allow_html=True)

    # Recommendations
    st.markdown("### 💡 Recommendations")
    for rec in data.get("recommendations", []):
        st.markdown(f'<div class="rec-item">→ {rec}</div>', unsafe_allow_html=True)

    render_architecture_graph(data)


def render_architecture_graph(data: dict):
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ⚙️ System Execution Trace")
    st.markdown("<small style='color:#86868b;'>Live trace of the backend pipeline for this claim.</small>", unsafe_allow_html=True)

    flow = data.get("execution_flow", [])
    if flow:
        graph_code = 'digraph G {\n'
        graph_code += '  rankdir="TB";\n'
        graph_code += '  node [shape=box, style="filled,rounded", fillcolor="#f5f5f7", color="#d2d2d7", fontname="Inter", fontcolor="#1d1d1f", fontsize=10, width=3.2, height=0.55];\n'
        graph_code += '  edge [color="#0071e3", penwidth=1.8, arrowsize=0.7];\n'
        graph_code += '  bgcolor="transparent";\n\n'

        for i, step in enumerate(flow):
            node_id = f"node_{i}"
            label = f"{step['node']}\\n{step['label']}\\n({step['detail']})"
            graph_code += f'  {node_id} [label="{label}"];\n'
            if i > 0:
                graph_code += f'  node_{i-1} -> {node_id};\n'

        graph_code += "}\n"
        st.graphviz_chart(graph_code, use_container_width=True)


USER_DB_PATH = "data/users.json"

def load_users():
    if not os.path.exists(USER_DB_PATH):
        default_users = {"admin": "password"}
        os.makedirs(os.path.dirname(USER_DB_PATH), exist_ok=True)
        with open(USER_DB_PATH, "w") as f:
            json.dump(default_users, f)
        return default_users
    with open(USER_DB_PATH, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB_PATH, "w") as f:
        json.dump(users, f)

def auth_page():
    st.markdown('<div class="hero-title" style="font-size:2.2rem; margin-top:2rem;">Welcome Back</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Login or create an account to continue</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            l_username = st.text_input("Username", key="login_user")
            l_password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True, key="btn_login"):
                users = load_users()
                if l_username in users and users[l_username] == l_password:
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = l_username
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            r_username = st.text_input("New Username", key="reg_user")
            r_password = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Register", use_container_width=True, key="btn_register"):
                users = load_users()
                if not r_username or not r_password:
                    st.error("Please fill in both fields")
                elif r_username in users:
                    st.error("Username already exists!")
                else:
                    users[r_username] = r_password
                    save_users(users)
                    st.success("Registration successful! You can now log in.")

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    render_header()

    if not st.session_state["logged_in"]:
        auth_page()
        return

    current_user = st.session_state.get("current_user", "unknown")
    st.markdown(f'<div style="text-align: right; color: #86868b; font-size: 0.85rem;">Logged in as <b>{current_user}</b></div>', unsafe_allow_html=True)

    submitted, claim_data = render_form()

    if submitted:
        empty_fields = []
        for key, val in claim_data.items():
            if val == "" or val is None:
                display_name = key.replace("_", " ").title()
                empty_fields.append(display_name)

        if empty_fields:
            st.warning(f"⚠️ Please fill in the following required field(s): {', '.join(empty_fields)}")
            return

        with st.spinner("Analyzing claim..."):
            try:
                response = requests.post(f"{API_URL}/predict-claim", json=claim_data, timeout=30)
                if response.status_code == 200:
                    render_results(response.json())
                elif response.status_code == 422:
                    st.error(f"Validation Error: {response.json().get('detail', 'Invalid input')}")
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except requests.ConnectionError:
                st.error("Cannot connect to the API server. Make sure the FastAPI backend is running on port 8000.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
