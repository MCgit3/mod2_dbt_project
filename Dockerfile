# Start with a lightweight Python image
FROM python:3.11-slim

# Install dbt-bigquery and expectations
RUN pip install --no-cache-dir dbt-bigquery==1.11.1 dbt-expectations

# Install analysis dependencies
RUN pip install --no-cache-dir streamlit pandas plotly jupyter papermill

WORKDIR /app

# Copy your dbt project + notebooks
COPY . /app

# Environment variables
ENV DBT_PROFILES_DIR=/app

# Install dbt packages
RUN dbt deps

# Default command
CMD ["dbt", "run"]
