
def parse_valor_monetario(valor) -> float:
    if valor is None: return 0.0
    if isinstance(valor, (float, int)): return float(valor)
    if isinstance(valor, str):
        limpo = valor.replace("R$", "").strip()
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return 0.0
    return 0.0