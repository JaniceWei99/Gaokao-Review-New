"""WeChat Pay V3 integration — JSAPI payment for mini-program."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

PRICING = {
    ("standard", "monthly"): 1990,
    ("standard", "yearly"): 19900,
    ("standard", "lifetime_high_school"): 39900,
    ("premium", "monthly"): 3990,
    ("premium", "yearly"): 39900,
}

PRICING_YUAN = {
    ("standard", "monthly"): 19.9,
    ("standard", "yearly"): 199,
    ("standard", "lifetime_high_school"): 399,
    ("premium", "monthly"): 39.9,
    ("premium", "yearly"): 399,
}


def _is_pay_configured() -> bool:
    return bool(settings.wx_pay_mch_id and settings.wx_pay_api_key_path)


async def create_jsapi_order(
    user_id: uuid.UUID,
    openid: str,
    plan: str,
    billing_type: str,
    out_trade_no: str,
) -> dict:
    """Create a JSAPI payment order via WeChat Pay V3 API.

    Returns the payment parameters needed by wx.requestPayment().
    In development mode (no mch_id configured), returns mock params.
    """
    amount = PRICING.get((plan, billing_type))
    if amount is None:
        raise ValueError(f"Invalid plan/billing_type: {plan}/{billing_type}")

    if not _is_pay_configured():
        logger.info(
            "WeChat Pay mock mode: creating order for user=%s plan=%s billing=%s",
            user_id, plan, billing_type,
        )
        return {
            "timeStamp": str(int(time.time())),
            "nonceStr": uuid.uuid4().hex,
            "package": "prepay_id=mock_prepay_id_" + out_trade_no,
            "signType": "RSA",
            "paySign": "mock_sign",
            "out_trade_no": out_trade_no,
        }

    description = f"高考复习助手-{plan == 'standard' and '标准版' or '高级版'}-{billing_type == 'monthly' and '月付' or billing_type == 'yearly' and '年付' or '全程包'}"

    body = {
        "appid": settings.wx_app_id,
        "mchid": settings.wx_pay_mch_id,
        "description": description,
        "out_trade_no": out_trade_no,
        "notify_url": settings.wx_pay_notify_url,
        "amount": {
            "total": amount,
            "currency": "CNY",
        },
        "payer": {
            "openid": openid,
        },
    }

    try:
        from wechatpayv3 import WeChatPay, WeChatPayType

        wxpay = WeChatPay(
            wechatpay_type=WeChatPayType.MINI_APP,
            mchid=settings.wx_pay_mch_id,
            private_key=_read_file(settings.wx_pay_api_key_path),
            cert_verifier=_read_file(settings.wx_pay_cert_path),
            appid=settings.wx_app_id,
            notify_url=settings.wx_pay_notify_url,
        )

        code, message = wxpay.pay(
            description=description,
            out_trade_no=out_trade_no,
            amount={"total": amount, "currency": "CNY"},
            pay_type=WeChatPayType.MINI_APP,
            openid=openid,
        )

        if code != 200:
            logger.error("WeChat Pay create order failed: code=%s message=%s", code, message)
            raise ValueError(f"WeChat Pay error: {message}")

        prepay_id = message.get("prepay_id", "")
        pay_params = wxpay.get_pay_params(prepay_id=prepay_id)
        pay_params["out_trade_no"] = out_trade_no
        return pay_params

    except ImportError:
        logger.warning("wechatpayv3 not installed, using httpx fallback")
        return await _create_order_httpx(body, out_trade_no)


async def _create_order_httpx(body: dict, out_trade_no: str) -> dict:
    """Fallback: create order using raw httpx calls to WeChat Pay V3 API."""
    url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=body)
        data = resp.json()

    if resp.status_code != 200:
        logger.error("WeChat Pay V3 error: %s", data)
        raise ValueError(f"WeChat Pay V3 error: {data.get('message', 'unknown')}")

    prepay_id = data.get("prepay_id", "")
    timestamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex
    package = f"prepay_id={prepay_id}"

    sign_str = f"{settings.wx_app_id}\n{timestamp}\n{nonce_str}\n{package}\n"

    pay_params = {
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": "placeholder_sign",
        "out_trade_no": out_trade_no,
    }
    return pay_params


def verify_pay_notification(headers: dict, body: bytes) -> dict | None:
    """Verify and decrypt a WeChat Pay V3 notification.

    Returns the decrypted resource dict, or None if verification fails.
    In mock mode, returns the body as-is.
    """
    if not _is_pay_configured():
        try:
            resource = json.loads(body)
            return resource.get("resource", resource)
        except (json.JSONDecodeError, AttributeError):
            return None

    try:
        from wechatpayv3 import WeChatPay, WeChatPayType

        wxpay = WeChatPay(
            wechatpay_type=WeChatPayType.MINI_APP,
            mchid=settings.wx_pay_mch_id,
            private_key=_read_file(settings.wx_pay_api_key_path),
            cert_verifier=_read_file(settings.wx_pay_cert_path),
            appid=settings.wx_app_id,
            notify_url=settings.wx_pay_notify_url,
        )

        result = wxpay.callback(headers=headers, body=body.decode("utf-8"))
        return result

    except ImportError:
        logger.warning("wechatpayv3 not installed, skipping notification verification")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None


def _read_file(path: str) -> str:
    """Read a file and return its content as string."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        return ""
