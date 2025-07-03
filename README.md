# FairAI Resume Screening

FairAI is a **modular, production-grade resume screening pipeline** that combines **FastAPI**, **Streamlit**, **Redis**, and a trained **XGBoost** machine learning model to automate the evaluation of candidate resumes. It empowers recruiters and HR teams to seamlessly ingest, process, score, and visualize resume data through interactive and explainable dashboards.

This project features:

- Real-time resume ingestion via Redis streams
- A trained XGBoost classification model for candidate evaluation and scoring
- FastAPI microservice for robust, scalable REST endpoints
- Streamlit dashboards for intuitive, HR-friendly data exploration and analytics
- Optional GPT-based resume summarization with LLM support
- Containerized orchestration with Docker for consistent local and cloud deployments
- End-to-end, event-driven architecture supporting extensibility and modular improvements


<br>
<img width="1464" alt="Screenshot 1" src="https://github.com/user-attachments/assets/aec93d7b-9077-48bf-91ec-139e2b7ee69a" />

<br><br><br>

<img width="1465" alt="Screenshot 2" src="https://github.com/user-attachments/assets/14c5fb89-a61b-417d-8601-4e4dba15029a" />

<br><br><br>

---

## Features

### Resume Ingestion
- Add candidate resumes via an intuitive Streamlit form  
- Supports manual data entry and PDF uploads  
- Submitted resumes are pushed to a Redis stream for downstream processing  
- Redis Streams simulate a real-time resume queue

### Resume Processing & Scoring
- Resumes are consumed from Redis and processed using FastAPI  
- Candidate details such as name, email, experience, skills, education, certifications, and job role are stored  
- An **AI score** is generated with a trained XGBoost classification model based on features like experience, project count, and education
- Final decision (`Hire` or `Reject`) is tracked for each resume and saved in Redis

### Machine Learning Model
- Includes a trained XGBoost model:
  - **xgb_resume_model.pkl** : serialized trained XGBoost binary  
  - **xgb_resume_model.json** : human-readable XGBoost configuration  
- Predicts a suitability score for each resume  
- The pipeline is designed to easily swap in future advanced models if needed

### Resume Summarization (Optional)
- Supports uploading PDF resumes  
- Extracts text from uploaded resumes  
- Optionally summarizes resumes with GPT (OpenAI) and shows the summary in the sidebar  
- Summarization is *optional* and can be disabled if you do not have OpenAI credits

### Interactive Analytics Dashboard
- Modern interactive dashboard built with Streamlit  
- Advanced filtering by:
  - Candidate name
  - Hire/reject decision
  - Education level
  - Job role
- Data visualization with:
  - Violin plots of AI scores
  - Stacked bar plots of decisions by education
  - Pair plots of numerical features
  - Pie charts of hire/reject rates
  - Bar charts for top 10 skills
  - Correlation heatmaps
  - Box plots for salary expectations
- CSV download for filtered results
- Clean dark-themed graphs with Plotly and Seaborn
- Responsive multi-column layout

### Modular Architecture
- **FastAPI** powers the backend  
- **Redis** acts as a fast, lightweight stream buffer  
- **Streamlit** handles the user-friendly dashboard  
- **XGBoost** classifies resumes and returns suitability scores  
- **LLM** provides optional semantic resume summaries  
- All components are Docker-ready

---

## Folder Structure

```plaintext
fairai-resume-screening/
├── main.py                   # FastAPI backend
├── dashboard.py              # Streamlit dashboard with Redis
├── dashboard_csv.py          # Standalone Streamlit dashboard with CSV fallback
├── xgb_resume_model.pkl      # Trained XGBoost model binary
├── xgb_resume_model.json     # Trained XGBoost model config
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── resume_data.csv           # Sample data
└── README.md
```



---

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/ashmita-web/fairai-resume-screening.git
cd fairai-resume-screening
```

2. Install dependencies
Make sure you have Python 3.9+ and Docker installed. Then install requirements:
```bash
pip install -r requirements.txt
```
3. Start Redis
If using Docker:
```bash
docker run -d --name redis -p 6379:6379 redis
```
Or via Homebrew on Mac:
```bash
brew services start redis
```
4. Start the FastAPI backend
```bash
uvicorn main:app --reload
```
6. Start the Streamlit dashboard
```bash
streamlit run dashboard.py
```
This will launch at http://localhost:8501

---

## How to Deploy

You can deploy this project in several ways:

1. Docker Compose (local all-in-one):
Use the included docker-compose.yml to launch Redis, FastAPI, and Streamlit containers together.
```bash
docker compose up --build
```
2. Render or other PaaS (FastAPI only):
Deploy your FastAPI endpoint on a cloud platform (e.g., Render, Railway) and connect a Streamlit Cloud deployment for the dashboard.

3. Streamlit Cloud:

For a static CSV-based dashboard (dashboard_csv.py), push to GitHub and link to streamlit.io cloud.


## Environment Variables

If you plan to use the LLM summarization features, set your environment variable:
```bash
export OPENAI_API_KEY=your_api_key_here
```
Otherwise, you can disable the LLM summary part in the code if you have no credits.

---
## Future Enhancements

- Add user authentication  
- Extend job role taxonomy  
- Integrate more advanced resume ranking models  
- Add a database for permanent resume storage (e.g., PostgreSQL)  

---

## Credits

Developed by Ashmita Luthra.
<br>
If you use this code or build upon it, please consider giving credit or referencing the GitHub repository.
