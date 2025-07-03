from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import xgboost as xgb
import numpy as np
import redis
from dotenv import load_dotenv
load_dotenv()
from mail import send_hire_email
import os
api_key = os.getenv("SENDGRID_API_KEY")
# Initialize FastAPI
app = FastAPI()

# Load XGBoost model
booster = xgb.Booster()
booster.load_model("xgb_resume_model.json")

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# schema
class ResumeData(BaseModel):
    experience: int
    projects_count: int
    ai_score: int
    salary_expectation: int
    skills: List[str]
    education: str
    certifications: Optional[str]
    job_role: str

# skill keywords
skill_keywords = [
    'c++', 'cybersecurity', 'deep learning', 'ethical hacking', 'java', 'linux',
    'machine learning', 'networking', 'nlp', 'python', 'pytorch', 'react', 'sql', 'tensorflow'
]
# education categories
edu_options = ['BSC', 'BTECH', 'MBA', 'MTECH', 'PHD']
# role categories
role_options = ['AI Researcher', 'Cybersecurity Analyst', 'Data Scientist', 'Software Engineer']

# main predictor
def predict_from_data(data: ResumeData) -> str:
    user_skills = [s.lower() for s in data.skills]
    skill_features = [1 if skill in user_skills else 0 for skill in skill_keywords]
    edu_onehot = [1 if data.education.upper() == e else 0 for e in edu_options]
    role_onehot = [1 if data.job_role == r else 0 for r in role_options]
    has_certification = 0 if data.certifications is None or data.certifications.lower() == "none" else 1

    feature_vector = np.array([[
        data.experience,
        data.salary_expectation,
        data.projects_count,
        data.ai_score,
        *skill_features,
        *edu_onehot,
        *role_onehot,
        has_certification
    ]])

    feature_names = [
        'Experience (Years)',
        'Salary Expectation ($)',
        'Projects Count',
        'AI Score (0-100)',
        'c++', 'cybersecurity', 'deep learning', 'ethical hacking', 'java', 'linux',
        'machine learning', 'networking', 'nlp', 'python', 'pytorch', 'react', 'sql', 'tensorflow',
        'Edu_BSC', 'Edu_BTECH', 'Edu_MBA', 'Edu_MTECH', 'Edu_PHD',
        'Role_AI Researcher', 'Role_Cybersecurity Analyst', 'Role_Data Scientist', 'Role_Software Engineer',
        'Has_Certification'
    ]

    dmatrix = xgb.DMatrix(feature_vector, feature_names=feature_names)
    prediction = booster.predict(dmatrix)
    return "Hire" if prediction[0] >= 0.5 else "Reject"


@app.on_event("startup")
async def startup_event():
    print("✅ FastAPI started and Redis connected.")


@app.post("/predict")
def predict_resume(data: ResumeData):
    try:
        decision = predict_from_data(data)
        return {"decision": decision}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def read_resumes_from_stream():
    while True:
        try:
            # block forever for new data
            events = r.xread({"resumes_stream": "$"}, block=0)
            for stream_name, messages in events:
                for message_id, fields in messages:
                    print(f"📝 Consumed {message_id} with data {fields}")
                    try:
                        # safely get skills
                        skills_str = fields.get("skills", "")
                        skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]

                        # map to ResumeData
                        resume_data = ResumeData(
                            experience=int(fields.get("experience", 0)),
                            projects_count=int(fields.get("projects_count", 0)),
                            ai_score=int(fields.get("ai_score", 0)),
                            salary_expectation=int(fields.get("salary_expectation", 0)),
                            skills=skills_list,
                            education=fields.get("education", "BSC"),
                            certifications=fields.get("certifications", None),
                            job_role=fields.get("job_role", "Data Scientist")
                        )

                        # predict
                        decision = predict_from_data(resume_data)
                        print(f"✅ Prediction for resume: {decision}")

                        # store in Redis
                        r.hset(
                            f"resume_results:{message_id}",
                            mapping={**fields, "decision": decision}
                        )
                        print(f"✅ Stored prediction under resume_results:{message_id}")

                        # email if HIRE
                        if decision == "Hire":
                            candidate_email = fields.get("email", None)
                            if candidate_email:
                                send_hire_email(
                                    to_email=candidate_email,
                                    candidate_name=fields.get("name", "Candidate")
                                )
                                print(f"📧 Email sent to {candidate_email} for HIRE candidate {fields.get('name')}")
                            else:
                                print("⚠️ No candidate email provided, skipping email alert")

                    except Exception as e:
                        print(f"❌ Error processing {message_id}: {e}")

        except redis.exceptions.ConnectionError as e:
            print(f"⚠️ Redis connection lost: {e} — retrying in 3 seconds...")
            import time
            time.sleep(3)
            continue


@app.get("/consume-resumes")
def consume_resumes(bg: BackgroundTasks):
    bg.add_task(read_resumes_from_stream)
    return {"message": "Redis stream consumer started."}

