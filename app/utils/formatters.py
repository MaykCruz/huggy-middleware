
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

def formatar_moeda(self, valor) -> str:
    """
    Converte float (1234.50) para formato BRL (R$ 1.234,50).
    Necessário pois o Service retorna float puro.
    """
    try:
        val = float(valor)
        us_fmt = f"{val:,.2f}"
        br_fmt = us_fmt.replace(',', 'X').replace('.', ',').replace('X', '.')
        return br_fmt
    except (ValueError, TypeError):
        return valor
