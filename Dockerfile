# FeedLab web app — for a VPS, Render, Railway, Hugging Face Spaces (Docker SDK), etc.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglu1-mesa && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8501
EXPOSE 8501
CMD streamlit run streamlit_app.py --server.port=${PORT} --server.address=0.0.0.0
