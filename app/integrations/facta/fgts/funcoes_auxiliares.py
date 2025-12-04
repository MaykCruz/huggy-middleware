from app.utils.formatters import parse_valor_monetario

def interpretar_retorno(data: dict) -> str:
    if not data.get("erro"):
        return "SUCESSO"
    
    code = data.get("codigo")
    msg = data.get("mensagem", "").lower()

    # Retorno genérico
    if "volte em" in msg: 
        return "WAITING_API"

    # Sem autorização
    if code == 7 or "instituição fiduciária não possui autorização do trabalhador" in msg:
        return "SEM_AUTORIZACAO"

    # Sem adesão
    if code == 9 or "trabalhador não possui adesão ao saque aniversário vigente" in msg: 
        return "SEM_ADESAO"

    # Mudanças cadastrais
    if code == 35 or "mudanças cadastrais na conta do fgts foram realizadas, que impedem a contratação" in msg: 
        return "MUDANCAS_CADASTRAIS"

    # Aniversariante
    termos_aniversariante = [
        "existe uma operação fiduciária em andamento",
        "operação não permitida antes de"
    ]

    if code in [5, 10] or any(termo in msg for termo in termos_aniversariante): 
        return "ANIVERSARIANTE"
    
    # Saldo não encontrado
    if code == 102 or "saldo não encontrado." in msg:
        return "SALDO_NAO_ENCONTRADO"

    # Sem saldo
    if code == 101 or "cliente não possui saldo fgts" in msg:
        return "SEM_SALDO"
        
    return "RETORNO_DESCONHECIDO"

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