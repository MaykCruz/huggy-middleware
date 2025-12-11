import httpx
import json
import os

# 1. Configuração
# Cole aqui a URL "RAW" do seu Gist (aquela mesma do .env)
GIST_URL = "https://gist.githubusercontent.com/MaykCruz/cfec635fda3b224f4715c90750da05f3/raw/messages.json"

# Caminho onde o arquivo local mora
OUTPUT_PATH = "app/services/bot/content/messages.json"

def sync():
    print(f"🔄 Conectando ao Gist...")
    
    try:
        # 2. Baixa o conteúdo
        response = httpx.get(GIST_URL)
        
        if response.status_code != 200:
            print(f"❌ Erro ao baixar: {response.status_code}")
            return

        data = response.json()
        
        # 3. Salva no disco (sobrescreve o local)
        # ensure_ascii=False garante que acentos fiquem corretos (não virem \u00e1)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Sucesso! O arquivo local foi atualizado com a versão do Gist.")
        print(f"📂 Caminho: {OUTPUT_PATH}")
        print("🚀 Agora basta dar 'git add' e 'git commit' para salvar no repositório.")

    except Exception as e:
        print(f"❌ Falha crítica: {e}")

if __name__ == "__main__":
    sync()