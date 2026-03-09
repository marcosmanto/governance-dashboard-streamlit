import base64
import io

import pyotp
import qrcode


def generate_mfa_secret() -> str:
    """Gera um segredo aleatório base32 para TOTP."""
    return pyotp.random_base32()


def get_totp_uri(username: str, secret: str, issuer_name: str = "GovernanceDashboard") -> str:
    """Gera a URI padrão para QR Codes."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)


def verify_totp(secret: str, code: str) -> bool:
    """Verifica se o código informado é válido para o segredo."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_qr_code_base64(uri: str) -> str:
    """Gera imagem do QR Code em base64 para exibir no frontend."""
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
