# Module 2 project Dockerfile
# Start with a lightweight Python image
FROM python:3.11-slim

# Install dbt-bigquery and expectations
RUN pip install --no-cache-dir dbt-bigquery==1.11.1

# Install analysis dependencies
RUN pip install --no-cache-dir \
    streamlit \
    pandas \
    numpy \
    plotly \
    matplotlib \
    seaborn \
    jupyter \
    papermill \
    google-cloud-bigquery

WORKDIR /app

# Copy your dbt project + notebooks
COPY . /app

# Environment variables
ENV DBT_PROFILES_DIR=/app

# Install dbt packages
RUN dbt deps

# Cloud Run provides PORT, normally 8080
CMD streamlit run app.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0
