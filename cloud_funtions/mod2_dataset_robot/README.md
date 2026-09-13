# mod2-dataset-robot

## Purpose

This Cloud Run Function checks the Kaggle Olist dataset for updates.

If new data is detected:

1. Download the Kaggle dataset
2. Upload CSV files to Cloud Storage
3. Load CSV files into BigQuery raw tables
4. Save the latest Kaggle update timestamp in GCS
5. Trigger the downstream data pipeline

## Cloud Run Function

Service name:

mod2-dataset-robot

Entry point:

import_kaggle_data

## Environment Variables

The following environment variables are required:

- KAGGLE_USERNAME
- KAGGLE_KEY
- BUCKET_NAME
- DATASET_ID

## Important

Do not store Kaggle credentials in GitHub.
Configure credentials using Cloud Run environment variables or Secret Manager.