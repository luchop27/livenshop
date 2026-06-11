import os

from .settings import *


PAYPHONE_TOKEN = os.getenv('PAYPHONE_TOKEN')
PAYPHONE_STORE_ID = os.getenv('PAYPHONE_STORE_ID')
PAYPHONE_CONFIRM_URL = os.getenv('PAYPHONE_CONFIRM_URL', 'https://paymentbox.payphonetodoesposible.com/api/confirm')
PAYPHONE_RESPONSE_URL = os.getenv('PAYPHONE_RESPONSE_URL')
PAYPHONE_CANCEL_URL = os.getenv('PAYPHONE_CANCEL_URL')

SECURE_REFERRER_POLICY = 'origin-when-cross-origin'