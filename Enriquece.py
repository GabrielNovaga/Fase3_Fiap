import pandas as pd
import requests
import time
import yfinance as yf
import numpy as np
cache = {}
cacheEps = {}
# Cache para armazenar os dados já baixados
cacheBalanceSheet = {}
cacheOverview = {}
datai = None
datag = None
datav = None
# 1. Ler o arquivo Excel com as colunas financeiras
file_path = "financial.xlsx"  # Atualize com o caminho correto do seu arquivo
df = pd.read_excel(file_path)

# 2. Selecionar os 5 indicadores financeiros mais importantes
#selected_columns = ['symbol', 'fiscalDateEnding', 'totalRevenue', 'grossProfit', 'operatingIncome', 'ebitda',
       #             'netIncome']
#df_selected = df[selected_columns].copy()  # Usar .copy() para evitar o problema de view/copy

df_selected = df

# Configurar sua chave da API Alpha Vantage (substitua 'YOUR_API_KEY' pela sua chave)
API_KEY = 'GFGJ4SA3CAJBPBKR'
base_url = 'https://www.alphavantage.co/query'


# Função para pegar o preço da ação duas semanas após a data do balanço
def get_stock_price(symbol, fiscal_date_ending):
    base_url = "https://www.alphavantage.co/query"

    # Fazer a requisição para pegar dados diários ajustados
    response = requests.get(
        f"{base_url}?function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol={symbol}&apikey={API_KEY}")
    data = response.json()

    try:
        # Pegar a data de duas semanas depois
        price_2_weeks_later = pd.to_datetime(fiscal_date_ending) + pd.DateOffset(weeks=2)

        # Formatar a data para o formato esperado pela API
        formatted_date = price_2_weeks_later.strftime('%Y-%m-%d')

        # Obter todas as datas disponíveis nos dados de retorno
        available_dates = pd.to_datetime(list(data['Time Series (Daily)'].keys())).sort_values(ascending=False)

        # Procurar o dia útil mais próximo anterior ou igual ao formatted_date
        closest_date = available_dates[available_dates <= pd.to_datetime(formatted_date)].min()

        # Se encontramos a data mais próxima, retornamos o preço de fechamento ajustado
        if not pd.isna(closest_date):
            closest_date_str = closest_date.strftime('%Y-%m-%d')
            return data['Time Series (Daily)'][closest_date_str]['4. close']
        else:
            return None
    except KeyError:
        return None


# Função para pegar a média móvel de 60 dias após o fiscal_date_ending
def get_yahoo_price(symbol, fiscal_date_ending):

    # Baixar os dados históricos da ação se não estiverem já carregados
    if symbol not in cache:
        # Se não estiver, baixar os dados e armazenar no cache
        cache[symbol] = yf.download(symbol, start="1990-01-01")

    data = cache[symbol]

    try:
        # Pegar a data de 200 dias antes da fiscal_date_ending
        start_date = pd.to_datetime(fiscal_date_ending) - pd.DateOffset(days=60)

        start_end = pd.to_datetime(fiscal_date_ending) + pd.DateOffset(days=60)

        # Filtrar os dados entre start_date e fiscal_date_ending
        data_filtered = data.loc[start_date:start_end]

        # Calcular a média móvel de 200 dias para a janela de dados
        if not data_filtered.empty:
            moving_average_200d = data_filtered['Close'].mean()
            return moving_average_200d

        else:
            return None
    except KeyError:
        return None

def get_gold_price(fiscal_date_ending):
    global datag

    if datag is None:
        response = requests.get(
        base_url + f"?function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol=XAUUSD&apikey={API_KEY}")
        datag = response.json()

    try:
        # Pegar a data de duas semanas depois
        price_2_weeks_later = pd.to_datetime(fiscal_date_ending) + pd.DateOffset(weeks=2)

        # Formatar a data para o formato esperado pela API
        formatted_date = price_2_weeks_later.strftime('%Y-%m-%d')

        # Obter todas as datas disponíveis nos dados de retorno
        available_dates = pd.to_datetime(list(datag['Time Series (Daily)'].keys())).sort_values(ascending=False)

        # Procurar o dia útil mais próximo anterior ou igual ao formatted_date
        closest_date = available_dates[available_dates <= pd.to_datetime(formatted_date)].min()

        # Se encontramos a data mais próxima, retornamos o preço de fechamento ajustado
        if not pd.isna(closest_date):
            closest_date_str = closest_date.strftime('%Y-%m-%d')
            return datag['Time Series (Daily)'][closest_date_str]['4. close']
        else:
            return None
    except KeyError:
        return None

import pandas as pd
import requests
import time

# Definir sua chave de API


# Cache para armazenar os dados já baixados
cacheSharesOutstanding = {}

def get_shares_outstanding(symbol, fiscal_date_ending):
    shares_outstanding_data = None

    if symbol not in cacheSharesOutstanding:
        url_is = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={API_KEY}'

        if response_is.status_code == 200:
            data_is = response_is.json()
            if 'quarterlyReports' in data_is:
                income_statements = pd.DataFrame(data_is['quarterlyReports'])
                print(income_statements)
                income_statements['fiscalDateEnding'] = pd.to_datetime(income_statements['fiscalDateEnding'])
                income_statements['commonStockSharesOutstanding'] = pd.to_numeric(income_statements['commonStockSharesOutstanding'], errors='coerce')
                shares_outstanding_data = income_statements.set_index('fiscalDateEnding')
                cacheSharesOutstanding[symbol] = shares_outstanding_data
            else:
                print(f"Não foram encontrados dados de income statement para {symbol}")
                return None
        else:
            print(f"Erro na requisição para {symbol}: {response_is.status_code}")
            return None

    else:
        shares_outstanding_data = cacheSharesOutstanding[symbol]

    try:
        fiscal_date = pd.to_datetime(fiscal_date_ending)
        closest_date = shares_outstanding_data.index[shares_outstanding_data.index <= fiscal_date].max()

        if not pd.isna(closest_date):
            return shares_outstanding_data.loc[closest_date, 'commonStockSharesOutstanding']
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter Shares Outstanding para {symbol} em {fiscal_date_ending}: {e}")
        return None




def get_book_value(symbol, fiscal_date_ending):
    total_shareholder_equity = None
    shares_outstanding = None

    # Verificar se os dados do balanço patrimonial já estão em cache
    if symbol not in cacheBalanceSheet:
        # URL da API do Alpha Vantage para obter o balanço patrimonial
        url_bs = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={API_KEY}'
        print(API_KEY)
        # Fazer a requisição HTTP
        response_bs = requests.get(url_bs)

        #input()
        if response_bs.status_code == 200:
            data_bs = response_bs.json()
            if 'annualReports' in data_bs:
                # Criar DataFrame com os balanços trimestrais
                balance_sheet = pd.DataFrame(data_bs['annualReports'])
                #print(balance_sheet)
                #input()
                # Converter a coluna de datas para datetime
                balance_sheet['fiscalDateEnding'] = pd.to_datetime(balance_sheet['fiscalDateEnding'])
                # Converter a coluna de totalShareholderEquity para numérico
                balance_sheet['totalShareholderEquity'] = pd.to_numeric(balance_sheet['totalShareholderEquity'], errors='coerce')
                # Armazenar em cache
                balance_sheet_data = balance_sheet.set_index('fiscalDateEnding')
                cacheBalanceSheet[symbol] = balance_sheet_data
            else:
                print(f"Não foram encontrados dados de balanço para {symbol}")
                return None
        else:
            print(f"Erro na requisição do balanço para {symbol}: {response_bs.status_code}")
            return None
        # Respeitar o limite de requisições da API (máximo de 5 por minuto)

    else:
        balance_sheet_data = cacheBalanceSheet[symbol]


    try:
        # Procurar o valor patrimonial para a data fiscal mais próxima anterior ou igual à data fornecida
        fiscal_date = pd.to_datetime(fiscal_date_ending)
        closest_date = balance_sheet_data.index[balance_sheet_data.index <= fiscal_date].max()

        if not pd.isna(closest_date):
            total_shareholder_equity = balance_sheet_data.loc[closest_date, 'totalShareholderEquity']
            #print(total_shareholder_equity)
            #input()
            return total_shareholder_equity
        else:
            return None, shares_outstanding
    except Exception as e:
        print(f"Erro ao obter dados para {symbol} em {fiscal_date_ending}: {e}")
        return None, None


def get_eps(symbol, fiscal_date_ending):
    earnings_data = None

    # Verificar se os dados já estão em cache
    if symbol not in cacheEps:
        # URL da API do Alpha Vantage para obter os earnings
        url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={symbol}&apikey={API_KEY}'

        # Fazer a requisição HTTP
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'annualEarnings' in data:
                # Criar DataFrame com os earnings trimestrais
                earnings = pd.DataFrame(data['annualEarnings'])
                #print(earnings)
                #input()
                # Converter as colunas de datas para datetime
                earnings['fiscalDateEnding'] = pd.to_datetime(earnings['fiscalDateEnding'])
                #earnings['reportedDate'] = pd.to_datetime(earnings['reportedDate'])
                # Converter a coluna de EPS para numérico
                earnings['reportedEPS'] = pd.to_numeric(earnings['reportedEPS'], errors='coerce')
                # Armazenar em cache
                earnings_data = earnings.set_index('fiscalDateEnding')
                cacheEps[symbol] = earnings_data
                # Respeitar o limite de requisições da API (máximo de 5 por minuto)

            else:
                print(f"Não foram encontrados dados de earnings para {symbol}")
                return None
        else:
            print(f"Erro na requisição para {symbol}: {response.status_code}")
            return None
    else:
        earnings_data = cacheEps[symbol]

    try:
        # Procurar o EPS para a data fiscal mais próxima anterior ou igual à data fornecida
        fiscal_date = pd.to_datetime(fiscal_date_ending)
        closest_date = earnings_data.index[earnings_data.index <= fiscal_date].max()

        if not pd.isna(closest_date):
            return earnings_data.loc[closest_date, 'reportedEPS']
        else:
            return None
    except Exception as e:
        print(f"Erro ao obter EPS para {fiscal_date_ending}: {e}")
        return None


def get_vix_price(fiscal_date_ending):
    global datav

    # Verificar se os dados já foram baixados; se não, baixar os dados históricos do VIX
    if datav is None:
        # Baixar os dados completos do VIX com yfinance
        datav = yf.download('^VIX', start="1990-01-01")

    try:
        # Pegar a data de duas semanas depois da fiscal_date_ending
        price_2_weeks_later = pd.to_datetime(fiscal_date_ending) + pd.DateOffset(weeks=2)

        # Procurar o dia útil mais próximo anterior ou igual ao formatted_date
        closest_date = datav.index[datav.index <= price_2_weeks_later].max()

        # Se encontramos a data mais próxima, retornamos o preço de fechamento
        if not pd.isna(closest_date):
            return datav.loc[closest_date, 'Close']
        else:
            return None
    except KeyError:
        return None

# Função para pegar a taxa de juros americana em uma data específica (mais próxima)
def get_interest_rate(date_str):
    global datai

    # Converter a data passada para o formato datetime
    target_date = pd.to_datetime(date_str)

    # Verificar se os dados já estão armazenados na variável global
    if datai is None:
        # Fazer a requisição para obter os dados da taxa de juros
        response = requests.get(f"{base_url}?function=FEDERAL_FUNDS_RATE&apikey={API_KEY}")
        datai = response.json()


    try:
        # Inicializar a variável para a data mais próxima
        closest_date = None
        closest_value = None

        # Iterar pela lista de dados retornada
        for entry in datai['data']:
            entry_date = pd.to_datetime(entry['date'])  # Converter a data da entrada para datetime

            # Encontrar a data mais próxima que seja menor ou igual à data alvo
            if entry_date <= target_date:
                if closest_date is None or entry_date > closest_date:
                    closest_date = entry_date
                    closest_value = entry['value']

        # Retornar o valor correspondente à data mais próxima
        return closest_value
    except KeyError:
        return None



df_existing = None
# Tentar carregar um arquivo existente para continuar de onde parou, se já houver um
output_file = 'financial_with_predictions.xlsx'

try:
    df_existing = pd.read_excel(output_file)
    # Localizar a última linha não processada
    last_processed_index = df_existing.last_valid_index()
    print(last_processed_index)

    # Remover colunas ou linhas completamente vazias do DataFrame existente, se houver
    df_existing = df_existing.dropna(how='all', axis=1)  # Remove colunas totalmente vazias
    df_existing = df_existing.dropna(how='all')  # Remove linhas totalme

    # Atualizar o DataFrame para incluir os dados existentes
    df_selected.update(df_existing)
except FileNotFoundError:
    last_processed_index = -1  # Começar do zero



# Iterar pelas linhas que ainda não foram processadas
for index, row in df_selected.iloc[last_processed_index + 1:].iterrows():
    # Pegar o preço da ação duas semanas depois
    stock = get_yahoo_price(row['symbol'], row['fiscalDateEnding'])
    print(index)
    print(row['symbol'])
    print(row['fiscalDateEnding'])
    print(stock)
    df_selected.loc[index, 'stock_price_mean'] = stock

    eps = get_eps(row['symbol'], row['fiscalDateEnding'])
    print("eps")
    print(eps)
    df_selected.loc[index, 'eps'] = eps
    #input()

    bv = get_book_value(row['symbol'], row['fiscalDateEnding'])
    print("book value")
    print(bv)

    if isinstance(bv, (list, np.ndarray, pd.Series)):
        if len(bv) == 1:
            bv_scalar = bv.iloc[0] if isinstance(bv, pd.Series) else bv[0]
        else:
            print(
                f"Vários valores encontrados para {row['symbol']} em {row['fiscalDateEnding']}. Usando o primeiro valor.")
            bv_scalar = bv.iloc[0] if isinstance(bv, pd.Series) else bv[0]
    else:
        bv_scalar = bv

    df_selected.loc[index, 'tsEquity'] = bv_scalar
    #input()

    #qt = get_shares_outstanding(row['symbol'], row['fiscalDateEnding'])
    #print("Share Out    ")
    #print(bv)
    #print(index)
    #print(row['symbol'])
    #print(row['fiscalDateEnding'])
    #df_selected.loc[index, 'shareOut'] = qt

    # Pegar a taxa de juros americana
    #interest = get_interest_rate(row['fiscalDateEnding'])
    #print(interest)
    #df_selected.loc[index, 'us_interest_rate'] = interest

    # Pegar o preço do ouro
    #gold = get_gold_price(row['fiscalDateEnding'])
    #print(gold)
    #df_selected.loc[index, 'gold_price'] = gold

    # Pegar o índice de volatilidade VIX
    #vix = get_vix_price(row['fiscalDateEnding'])
    #print(vix)
    #df_selected.loc[index, 'vix'] = vix

    # Verificar se a linha processada não é completamente vazia
    if not df_selected.iloc[[index]].isna().all().all():
        # Atualizar `df_existing` com os novos dados processados
        df_existing = pd.concat([df_existing, df_selected.iloc[[index]]], ignore_index=True)

    # Salvar os dados imediatamente após cada iteração
    df_existing.to_excel(output_file, index=False)

    # Esperar entre as requisições para evitar exceder o limite da API (no mínimo 12 segundos)
    #time.sleep(0.5)



# Exibir o DataFrame atualizado
print(df_selected.head())
