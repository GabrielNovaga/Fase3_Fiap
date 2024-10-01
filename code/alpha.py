import pandas as pd
import requests
import time
import os


# Função para carregar o arquivo Excel existente, se houver
def load_existing_data(file_name):
    if os.path.exists(file_name):
        return pd.read_excel(file_name)
    else:
        return pd.DataFrame()


# URL da tabela do S&P 500 na Wikipedia
url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# Ler a tabela da página
tables = pd.read_html(url)

# A tabela que contém os símbolos está normalmente na primeira posição
df_sp500 = tables[0]

# Extrair a lista de símbolos (tickers)
nsymbols = df_sp500['Symbol'].tolist()

# Carregar a lista de símbolos do arquivo Excel que você mencionou
file_path = 'links.xlsx'  # Arquivo que contém os tickers na coluna B
df_links = pd.read_excel(file_path)

# A coluna 'B' do Excel deve conter os tickers. Vou extrair essa coluna
tickers_from_excel = df_links.iloc[:, 1].dropna().tolist()  # Assume que os tickers estão na coluna B (índice 1)

# Lista original de symbols (que já existe no código)
#existing_symbols = nsymbols  # Esta variável 'symbols' já contém os símbolos carregados no seu código anterior

# Fazer a união dos símbolos, removendo duplicados
#symbols = list(set(nsymbols + tickers_from_excel))
symbols = list(set(nsymbols))
print(symbols)
# Defina sua API Key aqui (substitua 'demo' pela sua API Key real)
api_key = 'GFGJ4SA3CAJBPBKR'
#api_key = 'WZHEWBUQXA1OB8A6'


# Carregar o progresso anterior (se houver)
existing_file = 'sp500_income_statements.xlsx'
processed_data = load_existing_data(existing_file)

# Se houver dados existentes, filtrar os símbolos já processados
if not processed_data.empty:
    processed_symbols = processed_data['symbol'].unique().tolist()
    symbols = [symbol for symbol in symbols if symbol not in processed_symbols]

print(processed_data)
print(symbols)

# Loop sobre os símbolos restantes para coletar os dados financeiros
for symbol in symbols:
    # Lista para armazenar novos dados a cada execução
    new_data = []
    try:
        # Fazer a requisição para a API da Alpha Vantage
        url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={api_key}'

        response = requests.get(url)
        data = response.json()
        print(data)
        # Verificar se os dados contêm relatórios financeiros
        if 'annualReports' in data:

            for report in data['annualReports']:
                # Adicionar o símbolo da empresa ao relatório

                report['symbol'] = symbol
                new_data.append(report)

            # Após cada símbolo processado, salvar o progresso atual
        if new_data:
            # Converter a lista de novos dados para um DataFrame
            df_new = pd.DataFrame(new_data)

            # Concatenar com os dados existentes
            df_total = pd.concat([processed_data, df_new], ignore_index=True)

            processed_data = df_total

            # Salvar o DataFrame atualizado no arquivo Excel
            df_total.to_excel(existing_file, index=False)

            # Limpar a lista de novos dados já salvos
            new_data.clear()

        # Pausa para evitar atingir o limite de taxa da API
        time.sleep(1)  # Pausa de 12 segundos para não atingir o limite gratuito da API (5 chamadas/minuto)
        print(url)

    except Exception as e:
        print(f"Erro ao coletar dados para {symbol}: {e}")
        break  # Quebra o loop se houver erro, para reiniciar posteriormente



print(f"Dados atualizados e salvos em '{existing_file}'")
