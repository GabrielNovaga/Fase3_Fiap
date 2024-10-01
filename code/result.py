import pandas as pd
import matplotlib.pyplot as plt
import boto3
import pandas as pd
from io import StringIO

# Criar um cliente S3
s3 = boto3.client('s3')

# Nome do bucket e do arquivo
bucket_name = 'projetofiapteste123'
file_key = 'financial_pred.csv'  # Por exemplo: 'dados/meu_arquivo.csv'

client = boto3.client("s3", aws_access_key_id="retirado para subir no git",
                      aws_secret_access_key="retirado para subir no git",
                      aws_session_token="retirado para subir no git")

# Obter o objeto do S3
response = client.get_object(Bucket=bucket_name, Key=file_key)

# Ler o conteúdo do arquivo
content = response['Body'].read().decode('utf-8')

# Carregar o conteúdo em um DataFrame do pandas
df = pd.read_csv(StringIO(content))

# Exibir as primeiras linhas do DataFrame
print(df.head())

plt.figure(figsize=(12, 6))
plt.plot(df.index, df['stock_price_mean'],
         label='Preço Médio Real', color='blue')
plt.plot(df.index, df['predict'], label='Preço Previsto', color='red')
plt.title('Desempenho do Modelo de ML')
plt.xlabel('Observações')
plt.ylabel('Preço da Ação')
plt.legend()
plt.show()

# Gráfico de dispersão (target vs. features mais importantes)
plt.figure(figsize=(12, 6))
plt.scatter(df['stock_price_mean'], df['predict'], alpha=0.7)
plt.title('Regressão Linear: Preço Real vs. Previsão')
plt.xlabel('Preço Real')
plt.ylabel('Preço Previsão')
plt.plot([df['stock_price_mean'].min(), df['stock_price_mean'].max()], [
         df['stock_price_mean'].min(), df['stock_price_mean'].max()], 'k--', lw=2)
plt.show()
