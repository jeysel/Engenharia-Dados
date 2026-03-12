"""
Análise da Página 4 - Dados por município
"""
import pdfplumber

pdf_path = 'exemplo_boletim.pdf'

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[3]  # Página 4 (índice 3)

    print("PAGINA 4 - DADOS POR MUNICIPIO")
    print("=" * 80)

    # Extrair tabelas
    tables = page.extract_tables()
    print(f"\nTabelas encontradas: {len(tables)}\n")

    for idx, table in enumerate(tables):
        print(f"\nTABELA {idx + 1}:")
        print(f"Dimensoes: {len(table)} linhas x {len(table[0]) if table and len(table) > 0 else 0} colunas")

        if table and len(table) > 0:
            # Mostrar primeiras 20 linhas
            for row_idx, row in enumerate(table[:20]):
                print(f"  Linha {row_idx}: {row}")

            if len(table) > 20:
                print(f"  ... ({len(table) - 20} linhas restantes)")
