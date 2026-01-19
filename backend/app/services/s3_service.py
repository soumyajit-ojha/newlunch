import boto3
import uuid
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.utils.log_config import logger

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


class S3Service:
    @staticmethod
    def upload_image(file: UploadFile) -> str:
        try:
            extension = file.filename.split(".")[-1]
            file_key = f"products/{uuid.uuid4()}.{extension}"
            logger.info("S3 upload start: filename=%s key=%s", file.filename, file_key)

            s3_client.upload_fileobj(
                file.file,
                settings.AWS_S3_BUCKET_NAME,
                file_key,
                ExtraArgs={"ContentType": file.content_type},
            )

            url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            logger.info("S3 upload success: key=%s", file_key)
            return url
        except Exception as e:
            logger.error("S3 upload failed: filename=%s error=%s", file.filename, e)
            raise HTTPException(status_code=500, detail=f"S3 Upload failed: {str(e)}")
