import streamlit as st
import redis

# connect to redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

st.title("FairAI Resume Screening Dashboard")

# get all keys matching resume_results
keys = r.keys("resume_results:*")

if not keys:
    st.write("No resumes processed yet.")
else:
    for key in keys:
        data = r.hgetall(key)
        st.subheader(f"Resume ID: {key.split(':')[1]}")
        st.write(data)
