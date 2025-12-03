"""
Análise do arquivo XLS de Violência Doméstica
"""
import pandas as pd

arquivo = 'exemplo_violencia.xlsx'

try:
    # Ler arquivo Excel
    df = pd.read_excel(arquivo)

    print(f"Arquivo: {arquivo}")
    print(f"Dimensoes: {len(df)} linhas x {len(df.columns)} colunas\n")

    print("Colunas:")
    for idx, col in enumerate(df.columns):
        print(f"  {idx}: {col}")

    print(f"\nPrimeiras 10 linhas:")
    print(df.head(10).to_string())

    print(f"\nÚltimas 5 linhas:")
    print(df.tail(5).to_string())

    print(f"\nTipos de dados:")
    print(df.dtypes)

    print(f"\nValores unicos em algumas colunas:")
    for col in df.columns[:5]:  # Primeiras 5 colunas
        unique_values = df[col].nunique()
        print(f"  {col}: {unique_values} valores únicos")
        if unique_values < 10:
            print(f"    Valores: {df[col].unique()[:10]}")

except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
