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
    def upload_image(file: UploadFile, max_file_size: int = 5) -> str:
        """
        Uploads image with a file size limit.
        :param max_file_size: Size in MB (default 5MB)
        """
        try:
            max_bytes = max_file_size * 1024 * 1024
            file.file.seek(0, 2)  # Move to end of file
            file_size = file.file.tell()  # Get current position (size)
            file.file.seek(0)  # Reset to beginning for upload

            if file_size > max_bytes:
                logger.warning(
                    "S3 upload blocked: File too large (%s bytes)", file_size
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum allowed size is {max_file_size}MB.",
                )

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
        except HTTPException:
            # Re-raise the size exception so it's not caught by the generic block
            raise

        except Exception as e:
            logger.error("S3 upload failed: filename=%s error=%s", file.filename, e)
            raise HTTPException(status_code=500, detail=f"S3 Upload failed: {str(e)}")
