import streamlit as st
import redis
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import base64
from PyPDF2 import PdfReader
import openai
import os
import seaborn as sns
import plotly.express as px

# set your OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# connect to redis
r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)


st.set_page_config(page_title="FairAI Dashboard", layout="wide")
st.title("FairAI Resume Screening Dashboard")



# ------------ ADD NEW RESUME FORM -----------------------
st.sidebar.subheader("➕ Add New Resume")

with st.sidebar.form("add_resume_form"):
    name = st.text_input("Name")
    email = st.text_input("Candidate Email")
    experience = st.number_input("Experience (years)", min_value=0, max_value=50, value=0)
    projects_count = st.number_input("Projects Count", min_value=0, max_value=100, value=0)
    ai_score = st.slider("AI Score (0-100)", min_value=0, max_value=100, value=50)
    salary_expectation = st.number_input("Salary Expectation", min_value=0, max_value=1000000, value=0)
    skills = st.text_input("Skills (comma-separated)")
    education = st.selectbox("Education", ["BSC", "BTECH", "MBA", "MTECH", "PHD"])
    certifications = st.text_input("Certifications (leave blank if none)")
    job_role = st.selectbox("Job Role", ["AI Researcher", "Cybersecurity Analyst", "Data Scientist", "Software Engineer"])
    
    submitted = st.form_submit_button("Submit Resume")

    if submitted:
        resume_data = {
            "name": name,
            "email": email,
            "experience": str(experience),
            "projects_count": str(projects_count),
            "ai_score": str(ai_score),
            "salary_expectation": str(salary_expectation),
            "skills": skills,
            "education": education,
            "certifications": certifications if certifications else "None",
            "job_role": job_role
        }
        r.xadd("resumes_stream", resume_data)
        st.success("✅ Resume submitted to screening pipeline!")

# ------------ UPLOAD PDF RESUME -----------------------
uploaded_pdf = st.sidebar.file_uploader("📄 Upload PDF Resume", type="pdf")
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    
    st.sidebar.write("✅ Text extracted from PDF:")
    st.sidebar.write(text[:500] + "...")  # preview

    # ask GPT to summarize
    with st.spinner("Summarizing with LLM..."):
        summary = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert resume summarizer."},
                {"role": "user", "content": f"Summarize this resume:\n{text}"}
            ]
        )
        llm_summary = summary.choices[0].message.content
        st.sidebar.success("✅ Summary ready:")
        st.sidebar.write(llm_summary)


# ------------ LOAD RESULTS -----------------------------
keys = r.keys("resume_results:*")
results = []
for key in keys:
    data = r.hgetall(key)
    data["message_id"] = key.split(":")[1]
    results.append(data)

df = pd.DataFrame(results)

if df.empty:
    st.warning("No resumes processed yet.")
    st.stop()

# Convert numeric columns
numeric_cols = ["experience", "projects_count", "ai_score", "salary_expectation"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")


# --------------- FILTERS -----------------
st.sidebar.header(" Filters")

search_name = st.sidebar.text_input("Search by Name")
decision_filter = st.sidebar.selectbox("Filter by Decision", ["All", "Hire", "Reject"])
edu_filter = st.sidebar.selectbox("Filter by Education", ["All"] + sorted(df["education"].unique()))
role_filter = st.sidebar.selectbox("Filter by Job Role", ["All"] + sorted(df["job_role"].unique()))

filtered_df = df.copy()
if search_name:
    filtered_df = filtered_df[filtered_df["name"].str.contains(search_name, case=False)]
if decision_filter != "All":
    filtered_df = filtered_df[filtered_df["decision"] == decision_filter]
if edu_filter != "All":
    filtered_df = filtered_df[filtered_df["education"] == edu_filter]
if role_filter != "All":
    filtered_df = filtered_df[filtered_df["job_role"] == role_filter]




# --------------- DISPLAY TABLE --------------------------
st.subheader(" Resume Decisions")
st.dataframe(filtered_df)

# --------------- CSV DOWNLOAD --------------------------
csv = filtered_df.to_csv(index=False)
st.download_button("📥 Download CSV", csv, "resumes.csv", "text/csv")
st.write("Filtered columns present:", filtered_df.columns.tolist())

# set consistent theme
sns.set_theme(style="darkgrid", palette="pastel")

# dark theme for plotly
plotly_template = "plotly_dark"

# create Streamlit columns
col1, col2 = st.columns(2)

# =============== VIOLIN PLOT =================
with col1:
    st.subheader("🎻 AI Score Distribution by Decision")
    fig_violin = px.violin(
        filtered_df,
        x="decision",
        y="ai_score",
        color="decision",
        box=True,
        points="all",
        color_discrete_sequence=px.colors.qualitative.Set2,
        template=plotly_template
    )
    fig_violin.update_layout(height=400)
    st.plotly_chart(fig_violin, use_container_width=True)

# =============== STACKED BAR =================
with col2:
    st.subheader("Decision by Education")
    edu_decision = pd.crosstab(filtered_df["education"], filtered_df["decision"])
    edu_decision_norm = edu_decision.div(edu_decision.sum(axis=1), axis=0)
    fig_bar = px.bar(
        edu_decision_norm,
        orientation="h",
        barmode="stack",
        color_discrete_sequence=px.colors.qualitative.Set3,
        template=plotly_template
    )
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)


col3, col4 = st.columns(2)

# =============== PAIR PLOT =================
with col3:
    st.subheader(" Feature Relationships")
    selected_features = ["experience", "projects_count", "ai_score", "salary_expectation"]

    # filter columns that exist and are numeric
    valid_features = [
        col for col in selected_features
        if col in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[col])
    ]
    st.write("Valid features for pairplot:", valid_features)
    st.write("filtered_df[valid_features].shape:", filtered_df[valid_features].shape)
    st.write("filtered_df[valid_features].head():", filtered_df[valid_features].head())

    if len(valid_features) >= 2 and not filtered_df[valid_features].dropna().empty:
        pair_fig = sns.pairplot(
            filtered_df[valid_features].dropna(),
            corner=True,
            plot_kws={"alpha": 0.7}
        )
        st.pyplot(pair_fig)
    else:
        st.info("Not enough numeric data available for pair plot.")


# =============== HIRE RATE PIE =================
with col4:
    st.subheader("Hire Rate Overall")
    hire_rate = filtered_df["decision"].value_counts()
    fig_pie = px.pie(
        names=hire_rate.index,
        values=hire_rate.values,
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        template=plotly_template
    )
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

# =============== BAR CHART (COMMON SKILLS) =================
col5, col6 = st.columns(2)

with col5:
    st.subheader(" Top 10 Most Common Skills")
    all_skills = []
    for s in filtered_df["skills"]:
        all_skills.extend([i.strip().lower() for i in s.split(",")])
    skill_counts = Counter(all_skills)
    most_common_skills = dict(skill_counts.most_common(10))
    fig_skills = px.bar(
        x=list(most_common_skills.keys()),
        y=list(most_common_skills.values()),
        labels={"x": "Skill", "y": "Frequency"},
        color=list(most_common_skills.keys()),
        color_discrete_sequence=px.colors.qualitative.Set1,
        template=plotly_template
    )
    fig_skills.update_layout(height=400)
    st.plotly_chart(fig_skills, use_container_width=True)

# =============== AVG AI SCORE BY EDUCATION ================
with col6:
    st.subheader("Average AI Score by Education")
    filtered_df["ai_score"] = pd.to_numeric(filtered_df["ai_score"], errors="coerce")
    avg_score = filtered_df.groupby("education")["ai_score"].mean()
    fig_avg = px.bar(
        x=avg_score.index,
        y=avg_score.values,
        labels={"x": "Education", "y": "Average AI Score"},
        color=avg_score.index,
        color_discrete_sequence=px.colors.qualitative.Vivid,
        template=plotly_template
    )
    fig_avg.update_layout(height=400)
    st.plotly_chart(fig_avg, use_container_width=True)

# =============== ROW 3 — new plots ===============
col7, col8 = st.columns(2)

# =============== CORRELATION HEATMAP ================
with col7:
    st.subheader("Correlation Heatmap")

    corr = filtered_df[valid_features].corr()

    # explicitly set dark figure background
    fig_heat, ax_heat = plt.subplots(figsize=(5,4), facecolor="black")

    # plot with a color map suitable for dark background
    sns.heatmap(
        corr,
        annot=True,
        cmap="rocket",
        ax=ax_heat,
        cbar_kws={"label": "Correlation"},
        annot_kws={"color": "white"}
    )

    # set background colors
    ax_heat.set_facecolor("black")
    fig_heat.patch.set_facecolor("black")

    # set axis labels to white
    ax_heat.tick_params(colors="white")
    for label in ax_heat.get_xticklabels() + ax_heat.get_yticklabels():
        label.set_color("white")

    st.pyplot(fig_heat)


# =============== BOX PLOT ==========================
with col8:
    st.subheader("Salary Expectation by Decision")
    fig_box = px.box(
        filtered_df,
        x="decision",
        y="salary_expectation",
        color="decision",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)