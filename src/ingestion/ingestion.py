from src.utils.logger import setup_logger
from src.utils.settings import get_settings

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from boto3.exceptions import S3UploadFailedError
from pathlib import Path
import sys
from datetime import datetime


# -----------------------------------------------------------------------------
# Initial Setup
# -----------------------------------------------------------------------------

logger = setup_logger()
settings = get_settings()

LOCAL_FOLDER = Path("data/raw/29052026") # <-------------------Change this value

today = datetime.today()

year = today.strftime("%Y")
month = today.strftime("%m")
day = today.strftime("%d")

S3_PREFIX = (
    f"landing_zone/bicc_extract/"
    f"year={year}/month={month}/day={day}/"
)

# -----------------------------------------------------------------------------
# Validate Local Folder
# -----------------------------------------------------------------------------

if not LOCAL_FOLDER.exists():
    logger.error(f"Local folder does not exist: {LOCAL_FOLDER}")
    sys.exit(1)

if not LOCAL_FOLDER.is_dir():
    logger.error(f"Provided path is not a directory: {LOCAL_FOLDER}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Create S3 Client
# -----------------------------------------------------------------------------

try:
    logger.info("Creating AWS S3 client...")

    s3 = boto3.client(
        service_name="s3",
        region_name=settings.AWS_REGION_NAME,
        aws_access_key_id=settings.AWS_S3_SERVICE_ACC_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_S3_SERVICE_ACC_SECRET_KEY
    )

    logger.info("S3 client created successfully.")

except NoCredentialsError:
    logger.exception("AWS credentials not found.")
    sys.exit(1)

except ClientError as e:
    logger.exception(f"AWS client error occurred: {e}")
    sys.exit(1)

except Exception as e:
    logger.exception(f"Unexpected error while creating S3 client: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# Upload CSV Files
# -----------------------------------------------------------------------------

csv_files = list(LOCAL_FOLDER.glob("*.csv"))

if not csv_files:
    logger.warning(f"No CSV files found in {LOCAL_FOLDER}")
    sys.exit(0)

logger.info(f"Found {len(csv_files)} CSV files for upload.")

successful_uploads = 0
failed_uploads = 0

for file_path in csv_files:

    try:
        s3_key = f"{S3_PREFIX}{file_path.name}"

        logger.info(
            f"Uploading file: {file_path.name} "
            f"to s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}"
        )


        s3.upload_file(
                str(file_path),
                settings.AWS_S3_BUCKET_NAME,
                s3_key
        )


        successful_uploads += 1

        logger.info(
            f"Successfully uploaded: {file_path.name}"
        )

    except S3UploadFailedError as e:
        failed_uploads += 1

        logger.error(
            f"Failed to upload {file_path.name}: {e}"
        )

    except Exception as e:
        failed_uploads += 1

        logger.error(
            f"Unexpected error while uploading "
            f"{file_path.name}: {e}"
        )

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------

logger.info("Upload process completed.")

logger.info(
    f"Successful uploads: {successful_uploads}"
)

logger.info(
    f"Failed uploads: {failed_uploads}"
)