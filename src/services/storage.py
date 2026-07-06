import uuid

import boto3
from fastapi import UploadFile

from core.config import settings


class StorageService:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT_URL,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
        )
        self.bucket = settings.MINIO_BUCKET

    async def upload(self, file: UploadFile) -> str:
        contents = await file.read()
        extension = file.filename.rsplit(".", 1)[-1].lower()
        key = f"{uuid.uuid4().hex}.{extension}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=contents,
            ContentType=file.content_type,
        )
        return f"{settings.s3_public_url}/{key}"
