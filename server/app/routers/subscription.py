"""Subscription router — plan status, upgrade, and payment callback."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.subscription import SubscriptionResponse, UpgradeRequest
from app.services.payment_service import verify_pay_notification
from app.services.subscription_service import (
    get_subscription_status,
    handle_payment_callback,
    start_trial,
    upgrade_subscription,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=SubscriptionResponse)
async def get_subscription(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the current subscription status with limits."""
    return await get_subscription_status(user_id, db)


@router.post("/upgrade")
async def upgrade(
    body: UpgradeRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a subscription upgrade. Returns WeChat Pay parameters."""
    return await upgrade_subscription(user_id, body, db)


@router.post("/callback")
async def payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """WeChat Pay V3 notification callback.

    WeChat will POST here after payment completes.
    """
    headers = dict(request.headers)
    body = await request.body()

    resource = verify_pay_notification(headers, body)
    if resource is None:
        logger.warning("Payment callback verification failed")
        return {"code": "FAIL", "message": "Verification failed"}

    out_trade_no = resource.get("out_trade_no", "")
    trade_state = resource.get("trade_state", "")
    transaction_id = resource.get("transaction_id", "")

    await handle_payment_callback(out_trade_no, trade_state, db)

    return {"code": "SUCCESS", "message": "OK"}


@router.post("/start-trial", status_code=204)
async def begin_trial(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Start a 7-day free trial of the standard plan."""
    await start_trial(user_id, db)
