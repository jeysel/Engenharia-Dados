"""
Análise de todas as páginas buscando dados por município
"""
import pdfplumber

pdf_path = 'exemplo_boletim.pdf'

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total de paginas: {len(pdf.pages)}\n")

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()

        # Procurar por municípios conhecidos
        municipios = ['Florianopolis', 'Joinville', 'Blumenau', 'Chapeco', 'Itajai']
        municipios_encontrados = []

        for municipio in municipios:
            if municipio.upper() in text.upper():
                municipios_encontrados.append(municipio)

        # Procurar por palavras-chave de dados
        keywords = ['ROUBO', 'FURTO', 'HOMICIDIO', 'MUNICIPIO']
        keywords_encontradas = [k for k in keywords if k in text.upper()]

        if municipios_encontrados or 'MUNICIPIO' in text.upper():
            print(f"\nPAGINA {page_num + 1}:")
            print(f"  Municipios: {', '.join(municipios_encontrados) if municipios_encontrados else 'Nenhum especifico'}")
            print(f"  Keywords: {', '.join(keywords_encontradas)}")

            # Mostrar primeiras linhas de texto
            lines = text.split('\n')[:15]
            print(f"  Primeiras linhas:")
            for line in lines:
                if line.strip():
                    print(f"    {line.strip()}")
