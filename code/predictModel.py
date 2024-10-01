import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV
from boto3.s3.transfer import S3Transfer
import boto3


def dropOutliers(df):
    # Identificar outliers utilizando o método IQR
    Q1 = df.quantile(0.35)
    Q3 = df.quantile(0.65)
    IQR = Q3 - Q1
    outliers_condition = (df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))
    return df[~outliers_condition.any(axis=1)]


def sendToDataLake(df):
    client = boto3.client("s3", aws_access_key_id="retirado para subir no git",
                          aws_secret_access_key="retirado para subir no git",
                          aws_session_token="retirado para subir no git")

    # Salvar como .parquet
    df.to_csv('financial_pred.csv')

    transfer = S3Transfer(client)
    transfer.upload_file("financial_pred.csv",
                         "projetofiapteste123", "financial_pred.csv")
    print("dados salvo no s3 com sucesso!")


# Carregar o arquivo excel
file_path = "financial_with_predictions_bkp.xlsx"
df = pd.read_excel(file_path)

# reserva o dfprep para fazer previsão de uma outra planilha ou planilha inteira
dfpred = df


drop_columns = ['reportedCurrency', 'symbol', 'fiscalDateEnding', 'sellingGeneralAndAdministrative',
                'researchAndDevelopment', 'operatingExpenses',
                'investmentIncomeNet', 'netInterestIncome', 'interestIncome',
                'interestExpense', 'nonInterestIncome', 'otherNonOperatingIncome',
                'depreciation', 'depreciationAndAmortization',
                'incomeTaxExpense', 'interestAndDebtExpense',
                'netIncomeFromContinuingOperations', 'comprehensiveIncomeNetOfTax',
                'ebit']
df = df.sort_values('fiscalDateEnding', ascending=True)
df = df.drop(columns=drop_columns)
df = df.dropna()


# Gráfico de barras para identificar possíveis outliers
# plt.figure(figsize=(12, 6))
# sns.boxplot(data=df)
# plt.title('Boxplot das Features (Identificação de Outliers)')
# plt.xticks(rotation=90)
# plt.show()

df = dropOutliers(df)

# Separar os dados em features (X) e target (y)
X = df.drop(columns=['stock_price_mean'])
y = df['stock_price_mean']
print(X.describe())


# print(y)

# Normalizar os dados
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Dividir os dados em treino e teste (80% treino, 20% teste)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42)

# Redução de dimensionalidade
# pca = PCA(n_components=2)
# X_pca = pca.fit_transform(X_scaled)

# print(f"Variância explicada por cada componente: {pca.explained_variance_ratio_}")
# print(f"Variância explicada total: {sum(pca.explained_variance_ratio_)}")

# Treinar o modelo de regressão linear
# model = LinearRegression()
# model.fit(X_train, y_train)

# print(f"Melhores parâmetros: {grid_search.best_params_}")
# model = XGBRegressor(n_estimators=1000, learning_rate=0.05)
# model.fit(X_train, y_train)
# y_pred = model.predict(X_test)

# escolha do melhor finetinning
# param_grid = {
#    'n_estimators': [100, 200, 300],
#    'max_depth': [None, 10, 20, 30],
#    'min_samples_split': [2, 5, 10]
# }
# grid_search = GridSearchCV(RandomForestRegressor(), param_grid, cv=5)
# grid_search.fit(X_train, y_train)

model = RandomForestRegressor(
    n_estimators=100, max_depth=None, min_samples_split=2, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# Medir o desempenho do modelo
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# print(c)
# Exibir métricas de desempenho
print(f"Mean Squared Error (MSE): {mse}")
print(f"R-squared (R²): {r2}")
# input()

df_cleaned_pred = dfpred.dropna()
dfkeepcol = df_cleaned_pred
df_cleaned_pred = df_cleaned_pred.drop(columns=drop_columns)
# df_cleaned_pred = dropOutliers(df_cleaned_pred)
xpred = df_cleaned_pred.drop(columns=['stock_price_mean'])

x_scaled_pred = scaler.fit_transform(xpred)

df_cleaned_pred['predict'] = model.predict(x_scaled_pred)

coluna = df_cleaned_pred.pop('stock_price_mean')

# Inserir na penúltima posição
df_cleaned_pred.insert(len(df_cleaned_pred.columns) -
                       1, 'stock_price_mean', coluna)

output_file = "financial_with_predictions_and_forecasts.xlsx"
df_cleaned_pred = pd.concat([dfkeepcol, df_cleaned_pred], axis=1)
df_cleaned_pred.to_excel(output_file, index=False)
print(f"Previsões salvas no arquivo {output_file}.")

sendToDataLake(df_cleaned_pred)
