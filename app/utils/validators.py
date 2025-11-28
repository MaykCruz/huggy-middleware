import re

def validate_cpf(cpf: str) -> bool:
    """
    Valida se um CPF é válido (algoritmo de módulo 11).
    Retorna True se válido, False se inválido.
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)

    if len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11 é inválido mas passa no cálculo)
    if cpf == cpf[0] * len(cpf):
        return False

    # Cálculo do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[9]):
        return False

    # Cálculo do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[10]):
        return False

    return True

def clean_digits(text: str) -> str:
    """Retorna apenas os números da string"""
    return re.sub(r'[^0-9]', '', text)