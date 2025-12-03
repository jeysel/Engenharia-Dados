"""
Análise detalhada da Página 1 do PDF (Roubo e Furto)
"""
import pdfplumber
import pandas as pd

pdf_path = 'exemplo_boletim.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]  # Página 1

    print("=" * 80)
    print("ANÁLISE DETALHADA DA PÁGINA 1 - ROUBO E FURTO")
    print("=" * 80)

    # Extrair texto completo
    text = page.extract_text()
    print("\n--- TEXTO COMPLETO DA PÁGINA ---")
    print(text)
    print("\n" + "=" * 80)

    # Extrair tabelas
    tables = page.extract_tables()
    print(f"\n--- TABELAS ENCONTRADAS: {len(tables)} ---\n")

    for idx, table in enumerate(tables):
        print(f"\nTABELA {idx + 1}:")
        print(f"Dimensões: {len(table)} linhas x {len(table[0]) if table else 0} colunas")

        # Mostrar todas as linhas
        for row_idx, row in enumerate(table):
            print(f"  Linha {row_idx}: {row}")

        # Tentar converter para DataFrame
        try:
            if len(table) > 1:
                df = pd.DataFrame(table[1:], columns=table[0])
                print(f"\n  DataFrame criado com sucesso:")
                print(df.to_string())
        except Exception as e:
            print(f"\n  Erro ao criar DataFrame: {e}")

    print("\n" + "=" * 80)
    print("ANÁLISE DE PALAVRAS-CHAVE")
    print("=" * 80)

    # Procurar por palavras-chave
    keywords = ['ROUBO', 'FURTO', 'Município', 'Período', 'Ano']
    for keyword in keywords:
        if keyword.upper() in text.upper():
            print(f"✓ Encontrado: {keyword}")
            # Mostrar contexto
            lines = text.split('\n')
            for line_idx, line in enumerate(lines):
                if keyword.upper() in line.upper():
                    print(f"  Linha {line_idx}: {line.strip()}")
        else:
            print(f"✗ Não encontrado: {keyword}")
