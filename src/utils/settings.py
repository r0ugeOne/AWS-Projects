
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from functools import lru_cache
import os

# Load .env into the process environment (BaseSettings will also read env_file, but
# calling load_dotenv ensures values are available to other code and keeps behavior explicit)
load_dotenv()


class Settings(BaseSettings):

    AWS_S3_SERVICE_ACC_NAME: str
    AWS_S3_SERVICE_ACC_ACCESS_KEY: str
    AWS_S3_SERVICE_ACC_SECRET_KEY: str
    AWS_S3_BUCKET_NAME: str
    AWS_REGION_NAME: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    # Normalize legacy/alternate env names if present in the environment
    # e.g., some deployments may set `s3_service_acc_name` instead of
    # `AWS_S3_SERVICE_ACC_NAME`.
    if 's3_service_acc_name' in os.environ and 'AWS_S3_SERVICE_ACC_NAME' not in os.environ:
        os.environ['AWS_S3_SERVICE_ACC_NAME'] = os.environ['s3_service_acc_name']

    return Settings()
