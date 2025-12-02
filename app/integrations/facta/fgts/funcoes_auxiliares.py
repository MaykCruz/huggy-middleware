from app.utils.formatters import parse_valor_monetario

def interpretar_retorno(data: dict) -> str:
    if not data.get("erro"):
        return "SUCESSO"
    
    code = data.get("codigo")
    msg =data.get("mensagem", "").lower()

    if "volte em" in msg: return "WAITING_API"
    if code == 7: return "SEM_AUT"
    if code == 9: return "SEM_ADESAO"
    if code == 35: return "MUDANCAS_CADASTRAIS"
    if code in [5, 10]: return "ANIVERSARIANTE"
    if code in [101, 102, 104] or "não possui saldo" in msg or "não encontrado" in msg:
        return "SEM_SALDO"
        
    return "ERRO_GENERICO"

def organizar_parcelas(retorno_saldo: dict) -> list:
    parcelas = []
    encontrou_valida = False
    zerar = False

    for i in range(1, 6):
        data = retorno_saldo.get(f'dataRepasse_{i}')
        val_bruto = retorno_saldo.get(f'valor_{i}')

        if not data: break

        valor = parse_valor_monetario(val_bruto)

        if not encontrou_valida:
            if valor >= 100: encontrou_valida = True
        else:
            if valor < 100: zerar = True

        if zerar and encontrou_valida: valor = 0.0

        parcelas.append({f"dataRepasse_{i}": data, f"valor_{i}": valor})
        
    return parcelas

def selecionar_melhor_tabela(saldo_total: float) -> dict:
    """
    Define a melhor tabela e taxa com base no saldo do cliente.
    Retorna um dicionário com parâmetros para a API.
    """

    return {
        "codigo": 62170,
        "taxa": 1.80,
        "nome": "Gold Preference"
    }