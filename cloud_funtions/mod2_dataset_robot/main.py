import os
import shutil

import functions_framework
from google.cloud import storage
from google.cloud import bigquery


@functions_framework.http
def import_kaggle_data(request):

    # ============================================================
    # 1. READ ENVIRONMENT VARIABLES
    # ============================================================

    kaggle_username = os.environ.get("KAGGLE_USERNAME", "")
    kaggle_key = os.environ.get("KAGGLE_KEY", "")

    bucket_name = os.environ.get("BUCKET_NAME", "")
    dataset_id = os.environ.get("DATASET_ID", "")

    if not kaggle_username or not kaggle_key:
        return (
            "Error: KAGGLE_USERNAME or KAGGLE_KEY is missing!",
            400
        )

    if not bucket_name or not dataset_id:
        return (
            "Error: BUCKET_NAME or DATASET_ID is missing!",
            400
        )


    # ============================================================
    # 2. CONFIGURE KAGGLE ENVIRONMENT
    # ============================================================

    os.environ["KAGGLE_USERNAME"] = kaggle_username
    os.environ["KAGGLE_KEY"] = kaggle_key


    # ============================================================
    # 3. CREATE GOOGLE CLOUD CLIENTS
    # ============================================================

    storage_client = storage.Client()

    bucket = storage_client.bucket(
        bucket_name
    )

    bq_client = bigquery.Client()


    # ============================================================
    # 4. IMPORT KAGGLE
    # ============================================================

    import kaggle

    dataset_slug = "olistbr/brazilian-ecommerce"


    # ============================================================
    # 5. GET KAGGLE DATASET LAST UPDATED TIME
    # ============================================================

    try:

        print(
            "Checking Kaggle dataset metadata..."
        )

        datasets = kaggle.api.dataset_list(
            search="brazilian-ecommerce"
        )

        kaggle_last_updated = ""

        for dataset in datasets:

            dataset_ref = str(
                dataset.ref
            )

            print(
                f"Found Kaggle dataset: "
                f"{dataset_ref}"
            )

            # Find exactly our Olist dataset
            if dataset_ref == dataset_slug:

                kaggle_last_updated = str(
                    dataset.lastUpdated
                )

                print(
                    f"Kaggle dataset last updated on: "
                    f"{kaggle_last_updated}"
                )

                break


        # --------------------------------------------------------
        # Dataset was not found
        # --------------------------------------------------------

        if not kaggle_last_updated:

            return (
                f"Error: Could not find dataset "
                f"{dataset_slug} or its last update time!",
                500
            )


    except Exception as e:

        print(
            f"Failed to fetch Kaggle metadata: "
            f"{str(e)}"
        )

        return (
            f"Failed to fetch Kaggle metadata: "
            f"{str(e)}",
            500
        )


    # ============================================================
    # 6. CHECK LAST IMPORTED TIMESTAMP IN GCS
    # ============================================================

    timestamp_blob = bucket.blob(
        "last_updated.txt"
    )

    our_last_updated = ""

    if timestamp_blob.exists():

        our_last_updated = (
            timestamp_blob
            .download_as_text()
            .strip()
        )

        print(
            f"Our last imported version was from: "
            f"{our_last_updated}"
        )

    else:

        print(
            "last_updated.txt does not exist. "
            "Treating this as the first import."
        )


    # ============================================================
    # 7. COMPARE KAGGLE VERSION WITH LAST IMPORT
    # ============================================================

    if kaggle_last_updated == our_last_updated:

        print(
            "No changes detected on Kaggle. "
            "Skipping import."
        )

        return (
            "No changes detected on Kaggle. "
            "Pipeline skipped to save resources!",
            200
        )


    # ============================================================
    # 8. NEW DATA DETECTED
    # ============================================================

    print(
        "New Kaggle update detected! "
        "Starting dataset download..."
    )


    # ============================================================
    # 9. DOWNLOAD KAGGLE DATASET
    # ============================================================

    download_path = "/tmp/kaggle_data"

    try:

        # Remove old temporary data
        if os.path.exists(download_path):

            shutil.rmtree(
                download_path
            )


        # Create temporary directory
        os.makedirs(
            download_path,
            exist_ok=True
        )


        # Download and unzip Kaggle dataset
        kaggle.api.dataset_download_files(
            dataset_slug,
            path=download_path,
            unzip=True
        )

        print(
            "Kaggle dataset downloaded successfully."
        )


    except Exception as e:

        print(
            f"Failed to download Kaggle dataset: "
            f"{str(e)}"
        )

        return (
            f"Failed to download Kaggle dataset: "
            f"{str(e)}",
            500
        )


    # ============================================================
    # 10. FIND CSV FILES
    # ============================================================

    csv_files = []

    for file_name in os.listdir(download_path):

        if file_name.endswith(".csv"):

            csv_files.append(
                file_name
            )


    if not csv_files:

        return (
            "Error: No CSV files found "
            "in the Kaggle download!",
            400
        )


    print(
        f"Found {len(csv_files)} CSV files."
    )


    # ============================================================
    # 11. UPLOAD EACH CSV TO GCS
    #     THEN LOAD INTO BIGQUERY
    # ============================================================

    for csv_file in csv_files:


        # --------------------------------------------------------
        # Local file path
        # --------------------------------------------------------

        local_path = os.path.join(
            download_path,
            csv_file
        )

        blob_name = csv_file


        # --------------------------------------------------------
        # Upload CSV to GCS
        # --------------------------------------------------------

        print(
            f"Uploading {csv_file} to GCS..."
        )

        blob = bucket.blob(
            blob_name
        )

        blob.upload_from_filename(
            local_path
        )

        print(
            f"Successfully uploaded "
            f"{csv_file} to GCS."
        )


        # --------------------------------------------------------
        # Create BigQuery table name
        # --------------------------------------------------------

        table_name = (
            csv_file
            .replace(".csv", "")
            .replace("_dataset", "")
        )

        table_ref = (
            bq_client
            .dataset(dataset_id)
            .table(table_name)
        )


        # --------------------------------------------------------
        # BigQuery Load Configuration
        # --------------------------------------------------------

        job_config = bigquery.LoadJobConfig(

            source_format=(
                bigquery.SourceFormat.CSV
            ),

            skip_leading_rows=1,

            autodetect=True,

            allow_quoted_newlines=True,

            write_disposition=(
                bigquery.WriteDisposition.WRITE_TRUNCATE
            )
        )


        # --------------------------------------------------------
        # GCS URI
        # --------------------------------------------------------

        gcs_uri = (
            f"gs://{bucket_name}/{blob_name}"
        )


        # --------------------------------------------------------
        # Load GCS CSV into BigQuery
        # --------------------------------------------------------

        print(
            f"Loading {csv_file} into "
            f"BigQuery table {table_name}..."
        )

        load_job = (
            bq_client.load_table_from_uri(
                gcs_uri,
                table_ref,
                job_config=job_config
            )
        )


        # Wait until BigQuery loading finishes
        load_job.result()


        print(
            f"Successfully loaded BigQuery table: "
            f"{table_name}"
        )


    # ============================================================
    # 12. SAVE NEW KAGGLE TIMESTAMP
    # ============================================================

    timestamp_blob.upload_from_string(
        kaggle_last_updated
    )

    print(
        "Saved new Kaggle timestamp "
        "to last_updated.txt"
    )


    # ============================================================
    # 13. RETURN SUCCESS
    # ============================================================

    return (
        f"Success! Imported new dataset version from "
        f"{kaggle_last_updated}!",
        200
    )