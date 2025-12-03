"""
Script para analisar a estrutura de um PDF do boletim SSP-SC
"""
import pdfplumber
import json

pdf_path = 'exemplo_boletim.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total de páginas: {len(pdf.pages)}\n")

    for page_num, page in enumerate(pdf.pages):
        print(f"=" * 80)
        print(f"PÁGINA {page_num + 1}")
        print("=" * 80)

        # Extrair texto
        text = page.extract_text()
        if text:
            print("\n--- TEXTO DA PÁGINA (primeiras 500 chars) ---")
            print(text[:500])

        # Extrair tabelas
        tables = page.extract_tables()
        print(f"\n--- TABELAS ENCONTRADAS: {len(tables)} ---")

        for table_idx, table in enumerate(tables):
            print(f"\nTabela {table_idx + 1}:")
            print(f"  Dimensões: {len(table)} linhas x {len(table[0]) if table else 0} colunas")

            if table and len(table) > 0:
                print(f"  Cabeçalho: {table[0]}")

                if len(table) > 1:
                    print(f"  Primeira linha de dados: {table[1]}")

                if len(table) > 2:
                    print(f"  Segunda linha de dados: {table[2]}")

        print("\n")

        # Mostrar apenas as 3 primeiras páginas para análise
        if page_num >= 2:
            print("... (restante omitido)")
            break
