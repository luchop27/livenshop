from decimal import Decimal, ROUND_HALF_UP
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def to_cents(value):
    """Convierte un monto en decimal a centavos usando redondeo half-up."""
    return int((Decimal(value) * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _ensure_payphone_settings():
    missing = []
    if not settings.PAYPHONE_TOKEN:
        missing.append('PAYPHONE_TOKEN')
    if not settings.PAYPHONE_PREPARE_URL:
        missing.append('PAYPHONE_PREPARE_URL')
    if not settings.PAYPHONE_CONFIRM_URL:
        missing.append('PAYPHONE_CONFIRM_URL')
    if not settings.PAYPHONE_RESPONSE_URL:
        missing.append('PAYPHONE_RESPONSE_URL')
    if not settings.PAYPHONE_CANCEL_URL:
        missing.append('PAYPHONE_CANCEL_URL')

    if missing:
        raise ImproperlyConfigured(
            f"Faltan variables de entorno de PayPhone: {', '.join(missing)}"
        )


def preparar_pago_payphone(pedido):
    _ensure_payphone_settings()

    client_transaction_id = f"PEDIDO-{pedido.id}"
    payload = {
        'amount': to_cents(pedido.total),
        'amountWithoutTax': to_cents(pedido.total),
        'tax': 0,
        'clientTransactionId': client_transaction_id,
        'reference': f'Pedido #{pedido.id}',
        'responseUrl': settings.PAYPHONE_RESPONSE_URL,
        'cancellationUrl': settings.PAYPHONE_CANCEL_URL,
    }

    if settings.PAYPHONE_APP_ID:
        payload['appId'] = settings.PAYPHONE_APP_ID
    if settings.PAYPHONE_CLIENT_ID:
        payload['clientId'] = settings.PAYPHONE_CLIENT_ID
    if settings.PAYPHONE_CLIENT_SECRET:
        payload['clientSecret'] = settings.PAYPHONE_CLIENT_SECRET
    if settings.PAYPHONE_ENCODING_PASSWORD:
        payload['encodingPassword'] = settings.PAYPHONE_ENCODING_PASSWORD

    headers = {
        'Authorization': f'Bearer {settings.PAYPHONE_TOKEN}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        settings.PAYPHONE_PREPARE_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )
    safe_payload = payload.copy()
    safe_payload.pop("clientSecret", None)
    safe_payload.pop("encodingPassword", None)
    safe_payload.pop("clientId", None)
    safe_payload.pop("appId", None)
    print("PAYPHONE PAYLOAD SEGURO:", safe_payload, flush=True)
    print("PAYPHONE STATUS CODE:", response.status_code, flush=True)
    print("PAYPHONE RESPONSE TEXT:", response.text, flush=True)
    response.raise_for_status()
    data = response.json()

    pedido.payphone_client_transaction_id = client_transaction_id
    pedido.payphone_response = data
    pedido.save(update_fields=['payphone_client_transaction_id', 'payphone_response'])

    return data


def confirmar_pago_payphone(transaction_id, client_transaction_id):
    _ensure_payphone_settings()

    payload = {
        'id': transaction_id,
        'clientTransactionId': client_transaction_id,
    }

    if settings.PAYPHONE_APP_ID:
        payload['appId'] = settings.PAYPHONE_APP_ID
    if settings.PAYPHONE_CLIENT_ID:
        payload['clientId'] = settings.PAYPHONE_CLIENT_ID
    if settings.PAYPHONE_CLIENT_SECRET:
        payload['clientSecret'] = settings.PAYPHONE_CLIENT_SECRET
    if settings.PAYPHONE_ENCODING_PASSWORD:
        payload['encodingPassword'] = settings.PAYPHONE_ENCODING_PASSWORD

    headers = {
        'Authorization': f'Bearer {settings.PAYPHONE_TOKEN}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        settings.PAYPHONE_CONFIRM_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
