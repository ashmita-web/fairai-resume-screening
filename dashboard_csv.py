import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

st.set_page_config(page_title="FairAI Dashboard", layout="wide")
st.title("📊 FairAI Resume Screening Dashboard (CSV Mode)")

# load CSV
df = pd.read_csv("resume_data.csv")

# convert numeric
numeric_cols = ["experience", "projects_count", "ai_score", "salary_expectation"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# filters
st.sidebar.header("Filters")
decision_filter = st.sidebar.selectbox("Filter by Decision", ["All", "Hire", "Reject"])
if decision_filter != "All":
    df = df[df["decision"] == decision_filter]

# main table
st.subheader("Resume Data")
st.dataframe(df)

# violin plot
st.subheader("🎻 AI Score by Decision")
fig_violin = px.violin(
    df,
    x="decision",
    y="ai_score",
    color="decision",
    box=True,
    points="all",
    template="plotly_dark"
)
st.plotly_chart(fig_violin, use_container_width=True)

# stacked bar
st.subheader("📊 Education vs Decision")
edu_decision = pd.crosstab(df["education"], df["decision"])
edu_decision_norm = edu_decision.div(edu_decision.sum(axis=1), axis=0)
fig_bar = px.bar(
    edu_decision_norm,
    orientation="h",
    barmode="stack",
    template="plotly_dark"
)
st.plotly_chart(fig_bar, use_container_width=True)

# download
st.download_button(
    "Download CSV",
    data=df.to_csv(index=False),
    file_name="resumes.csv",
    mime="text/csv"
)
