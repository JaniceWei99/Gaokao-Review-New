"""Image upload API — generate COS temporary credentials for client-side upload."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user_id
from app.services.image_service import generate_image_key, get_upload_credentials

router = APIRouter()


class UploadCredentialRequest(BaseModel):
    prefix: str = Field(..., description="Storage prefix: errors or growth")
    extension: str = Field("jpg", description="File extension")
    student_id: uuid.UUID = Field(..., description="Student ID for path generation")


class UploadCredentialResponse(BaseModel):
    tmp_secret_id: str | None = None
    tmp_secret_key: str | None = None
    tmp_secret_token: str | None = None
    start_time: int | None = None
    expired_time: int | None = None
    bucket: str
    region: str
    image_key: str
    upload_url: str


@router.post("/image", response_model=UploadCredentialResponse)
async def request_upload_credential(
    body: UploadCredentialRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Generate COS temporary upload credentials for client-side direct upload."""
    image_key = generate_image_key(body.prefix, body.student_id, body.extension)
    creds = get_upload_credentials(image_key)
    return UploadCredentialResponse(**creds)
