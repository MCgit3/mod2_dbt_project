# Start with a lightweight Python image
FROM python:3.11-slim

# Install dbt-bigquery
RUN pip install --no-cache-dir dbt-bigquery==1.11.1

# Set working directory inside the container
WORKDIR /app

# Copy your dbt project files into the container
COPY . /app

# Tell dbt where to find your service account JSON
#ENV GOOGLE_APPLICATION_CREDENTIALS=/app/hale-badge-505304-j8-6583941cdaca.json

ENV DBT_PROFILES_DIR=/app

# Default command: run dbt when the container starts
CMD ["dbt", "run"]

