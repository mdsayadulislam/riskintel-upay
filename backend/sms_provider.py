"""
RiskIntel upay - SMS Provider Abstraction
File: backend/sms_provider.py

Provides an enterprise SMS delivery abstraction supporting:
1. TwilioSmsProvider: Real-world SMS delivery using Twilio REST API.
2. DevelopmentSmsProvider: Safe local console logging with phone masking (never logs raw OTP in production).
3. MockSmsProvider: For automated unit and integration tests.
"""

import abc
import logging
import os
import re
import urllib.parse
import urllib.request
import base64
import json
from typing import Dict, Any, Optional

logger = logging.getLogger("riskintel.sms")


class SmsDeliveryError(Exception):
    """Raised when an SMS provider fails to deliver a message."""
    pass


class BaseSmsProvider(abc.ABC):
    """Abstract base class for SMS notification delivery."""

    @abc.abstractmethod
    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Dispatches an SMS to the destination phone number.
        Returns a dictionary containing delivery metadata.
        """
        pass


class TwilioSmsProvider(BaseSmsProvider):
    """
    Twilio SMS Provider using native HTTP requests (no heavy external SDK required).
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid.strip()
        self.auth_token = auth_token.strip()
        self.from_number = from_number.strip()
        self.endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token or not self.from_number:
            raise SmsDeliveryError("Twilio credentials incomplete (missing ACCOUNT_SID, AUTH_TOKEN, or FROM_NUMBER).")

        payload = urllib.parse.urlencode({
            "To": to_phone,
            "From": self.from_number,
            "Body": message,
        }).encode("utf-8")

        req = urllib.request.Request(self.endpoint, data=payload, method="POST")
        auth_header = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", f"Basic {auth_header}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info("Twilio SMS sent successfully. SID: %s", data.get("sid"))
                return {
                    "provider": "twilio",
                    "status": "sent",
                    "message_id": data.get("sid"),
                    "destination": to_phone,
                }
        except Exception as e:
            logger.error("Twilio SMS delivery failed: %s", e)
            raise SmsDeliveryError(f"Twilio API error: {str(e)}")


class DevelopmentSmsProvider(BaseSmsProvider):
    """
    Development SMS provider that logs OTP dispatch to backend console.
    Strictly disallowed in production.
    """

    def __init__(self, is_production: bool = False):
        self.is_production = is_production

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        if self.is_production:
            raise SmsDeliveryError("DevelopmentSmsProvider cannot be used in a production environment!")

        masked_phone = to_phone[:5] + "****" + to_phone[-4:] if len(to_phone) >= 9 else "****"
        logger.info(
            "\n"
            "===========================================================\n"
            "  [DEVELOPMENT SMS DISPATCH] To: %s\n"
            "  %s\n"
            "===========================================================",
            masked_phone,
            message
        )
        return {
            "provider": "development_console",
            "status": "delivered_to_console",
            "destination": masked_phone,
        }


class MockSmsProvider(BaseSmsProvider):
    """
    In-memory SMS provider for automated testing without side effects.
    """

    def __init__(self):
        self.sent_messages = []

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        record = {
            "to_phone": to_phone,
            "message": message,
            "provider": "mock",
            "status": "delivered_mock",
        }
        self.sent_messages.append(record)
        return record


# Factory to get configured SMS provider
_global_sms_provider: Optional[BaseSmsProvider] = None


def get_sms_provider(
    provider_name: Optional[str] = None,
    is_production: bool = False,
) -> BaseSmsProvider:
    global _global_sms_provider
    if _global_sms_provider is not None:
        return _global_sms_provider

    provider = (provider_name or os.getenv("SMS_PROVIDER", "development")).lower()

    if provider == "twilio":
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        _global_sms_provider = TwilioSmsProvider(account_sid, auth_token, from_number)
    elif provider == "mock":
        _global_sms_provider = MockSmsProvider()
    else:
        _global_sms_provider = DevelopmentSmsProvider(is_production=is_production)

    return _global_sms_provider


def set_sms_provider(provider: BaseSmsProvider) -> None:
    """Sets the global SMS provider instance (useful for unit testing)."""
    global _global_sms_provider
    _global_sms_provider = provider
