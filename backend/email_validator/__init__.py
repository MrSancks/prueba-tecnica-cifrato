class EmailNotValidError(ValueError):
    pass


def validate_email(email: str, *args, **kwargs):
    if "@" not in email:
        raise EmailNotValidError("Formato de correo inválido")
    return type("EmailResult", (), {"email": email})()
