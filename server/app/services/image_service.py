"""Image upload service — COS temporary credentials and signed URLs."""

import uuid
from datetime import datetime, timedelta, timezone

from app.config import settings


def _cos_client():
    from qcloud_cos import CosS3Client

    return CosS3Client(
        {
            "SecretId": settings.cos_secret_id,
            "SecretKey": settings.cos_secret_key,
            "Region": settings.cos_region,
        }
    )


def generate_image_key(prefix: str, student_id: uuid.UUID, extension: str = "jpg") -> str:
    now = datetime.now(timezone.utc)
    file_id = uuid.uuid4().hex[:12]
    return f"{prefix}/{student_id}/{now.year}/{now.month:02d}/{file_id}.{extension}"


def get_upload_credentials(
    image_key: str,
    expires_seconds: int = 3600,
) -> dict:
    bucket = settings.cos_bucket
    region = settings.cos_region
    secret_id = settings.cos_secret_id
    secret_key = settings.cos_secret_key

    from qcloud_cos.sts import Sts

    config = {
        "url": "https://sts.tencentcloudapi.com/",
        "domain": "sts.tencentcloudapi.com",
        "duration_seconds": expires_seconds,
        "secret_id": secret_id,
        "secret_key": secret_key,
        "bucket": bucket,
        "region": region,
        "allow_prefix": image_key,
        "allow_actions": [
            "name/cos:PutObject",
            "name/cos:PostObject",
        ],
    }

    try:
        sts = Sts()
    except Exception:
        return _fallback_presigned_url(bucket, image_key, expires_seconds)

    try:
        response = sts.get_credential(config)
        credentials = response["credentials"]
        return {
            "tmp_secret_id": credentials["tmpSecretId"],
            "tmp_secret_key": credentials["tmpSecretKey"],
            "tmp_secret_token": credentials["sessionToken"],
            "start_time": response["startTime"],
            "expired_time": response["expiredTime"],
            "bucket": bucket,
            "region": region,
            "image_key": image_key,
            "upload_url": f"https://{bucket}.cos.{region}.myqcloud.com/{image_key}",
        }
    except Exception:
        return _fallback_presigned_url(bucket, image_key, expires_seconds)


def _fallback_presigned_url(
    bucket: str,
    image_key: str,
    expires_seconds: int,
) -> dict:
    client = _cos_client()
    upload_url = client.get_presigned_url(
        Method="PUT",
        Bucket=bucket,
        Key=image_key,
        Expired=expires_seconds,
    )
    return {
        "upload_url": upload_url,
        "image_key": image_key,
        "bucket": bucket,
        "region": settings.cos_region,
    }


def get_signed_url(image_key: str, expires_hours: int = 2) -> str:
    bucket = settings.cos_bucket
    client = _cos_client()
    url = client.get_presigned_url(
        Method="GET",
        Bucket=bucket,
        Key=image_key,
        Expired=expires_hours * 3600,
    )
    return url


def delete_image(image_key: str) -> None:
    bucket = settings.cos_bucket
    client = _cos_client()
    client.delete_object(Bucket=bucket, Key=image_key)
