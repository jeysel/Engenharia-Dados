"""
Sistema de Visualização de Dados da SSP-SC
Dashboard interativo com filtros e gráficos
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@postgres:5432/ssp_sc_db'
)

try:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    logger.info("Conexão com banco de dados estabelecida")
except Exception as e:
    logger.error(f"Erro ao conectar ao banco de dados: {e}")
    engine = None


def get_data_from_db() -> pd.DataFrame:
    """
    Busca dados do banco de dados

    Returns:
        DataFrame com os dados
    """
    if not engine:
        logger.warning("Engine não disponível, retornando dados de exemplo")
        return get_sample_data()

    try:
        query = """
        SELECT
            id,
            data_coleta,
            tipo_ocorrencia,
            municipio,
            regiao,
            periodo,
            quantidade,
            ano,
            mes
        FROM dados_seguranca
        ORDER BY data_coleta DESC
        """
        df = pd.read_sql(query, engine)
        logger.info(f"{len(df)} registros carregados do banco de dados")
        return df
    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        return get_sample_data()


def get_sample_data() -> pd.DataFrame:
    """
    Retorna dados de exemplo para demonstração

    Returns:
        DataFrame com dados de exemplo
    """
    import random

    municipios = [
        'Florianópolis', 'Joinville', 'Blumenau', 'São José',
        'Criciúma', 'Chapecó', 'Itajaí', 'Jaraguá do Sul',
        'Lages', 'Palhoça', 'Balneário Camboriú', 'Brusque'
    ]

    tipos_ocorrencia = [
        'Furto', 'Roubo', 'Homicídio', 'Lesão Corporal',
        'Tráfico de Drogas', 'Porte Ilegal de Arma',
        'Violência Doméstica', 'Estelionato'
    ]

    regioes = ['Grande Florianópolis', 'Norte', 'Vale do Itajaí', 'Sul', 'Oeste', 'Serra']

    dados = []
    for i in range(1000):
        dados.append({
            'id': i + 1,
            'data_coleta': datetime.now(),
            'tipo_ocorrencia': random.choice(tipos_ocorrencia),
            'municipio': random.choice(municipios),
            'regiao': random.choice(regioes),
            'periodo': f"{random.randint(2020, 2024)}",
            'quantidade': random.randint(1, 100),
            'ano': random.randint(2020, 2024),
            'mes': random.randint(1, 12)
        })

    return pd.DataFrame(dados)


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/dados')
def get_dados():
    """
    Endpoint para obter dados com filtros

    Query Parameters:
        - tipo_ocorrencia: Filtrar por tipo de ocorrência
        - municipio: Filtrar por município
        - regiao: Filtrar por região
        - ano: Filtrar por ano
        - mes: Filtrar por mês
    """
    try:
        df = get_data_from_db()

        # Aplicar filtros
        tipo_ocorrencia = request.args.get('tipo_ocorrencia')
        if tipo_ocorrencia:
            df = df[df['tipo_ocorrencia'] == tipo_ocorrencia]

        municipio = request.args.get('municipio')
        if municipio:
            df = df[df['municipio'] == municipio]

        regiao = request.args.get('regiao')
        if regiao:
            df = df[df['regiao'] == regiao]

        ano = request.args.get('ano')
        if ano:
            df = df[df['ano'] == int(ano)]

        mes = request.args.get('mes')
        if mes:
            df = df[df['mes'] == int(mes)]

        # Converter para formato JSON
        # Substituir NaN por None antes de converter
        df = df.where(pd.notna(df), None)
        dados = df.to_dict('records')

        # Converter datetime para string
        for dado in dados:
            if 'data_coleta' in dado and isinstance(dado['data_coleta'], datetime):
                dado['data_coleta'] = dado['data_coleta'].isoformat()

        return jsonify({
            'success': True,
            'total': len(dados),
            'dados': dados
        })

    except Exception as e:
        logger.error(f"Erro ao buscar dados: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filtros')
def get_filtros():
    """Endpoint para obter opções de filtros"""
    try:
        df = get_data_from_db()

        filtros = {
            'tipos_ocorrencia': sorted(df['tipo_ocorrencia'].unique().tolist()),
            'municipios': sorted(df['municipio'].unique().tolist()),
            'regioes': sorted(df['regiao'].unique().tolist()),
            'anos': sorted(df['ano'].unique().tolist()),
            'meses': sorted([m for m in df['mes'].unique().tolist() if pd.notna(m)])
        }

        return jsonify({
            'success': True,
            'filtros': filtros
        })

    except Exception as e:
        logger.error(f"Erro ao buscar filtros: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/estatisticas')
def get_estatisticas():
    """Endpoint para obter estatísticas gerais"""
    try:
        df = get_data_from_db()

        # Aplicar filtros se houver
        tipo_ocorrencia = request.args.get('tipo_ocorrencia')
        if tipo_ocorrencia:
            df = df[df['tipo_ocorrencia'] == tipo_ocorrencia]

        municipio = request.args.get('municipio')
        if municipio:
            df = df[df['municipio'] == municipio]

        regiao = request.args.get('regiao')
        if regiao:
            df = df[df['regiao'] == regiao]

        ano = request.args.get('ano')
        if ano:
            df = df[df['ano'] == int(ano)]

        estatisticas = {
            'total_ocorrencias': int(df['quantidade'].sum()),
            'total_registros': len(df),
            'municipios_afetados': int(df['municipio'].nunique()),
            'tipos_ocorrencia': int(df['tipo_ocorrencia'].nunique()),
            'media_por_municipio': float(df.groupby('municipio')['quantidade'].sum().mean())
        }

        return jsonify({
            'success': True,
            'estatisticas': estatisticas
        })

    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grafico/ocorrencias-por-tipo')
def grafico_ocorrencias_tipo():
    """Gráfico de ocorrências por tipo"""
    try:
        df = get_data_from_db()

        # Aplicar filtros
        municipio = request.args.get('municipio')
        if municipio:
            df = df[df['municipio'] == municipio]

        regiao = request.args.get('regiao')
        if regiao:
            df = df[df['regiao'] == regiao]

        ano = request.args.get('ano')
        if ano:
            df = df[df['ano'] == int(ano)]

        # Agrupar por tipo de ocorrência
        dados_agrupados = df.groupby('tipo_ocorrencia')['quantidade'].sum().sort_values(ascending=False)

        fig = px.bar(
            x=dados_agrupados.index,
            y=dados_agrupados.values,
            labels={'x': 'Tipo de Ocorrência', 'y': 'Quantidade'},
            title='Ocorrências por Tipo',
            color=dados_agrupados.values,
            color_continuous_scale='Reds'
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )

        return jsonify({
            'success': True,
            'grafico': fig.to_json()
        })

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grafico/ocorrencias-por-municipio')
def grafico_ocorrencias_municipio():
    """Gráfico de ocorrências por município"""
    try:
        df = get_data_from_db()

        # Aplicar filtros
        tipo_ocorrencia = request.args.get('tipo_ocorrencia')
        if tipo_ocorrencia:
            df = df[df['tipo_ocorrencia'] == tipo_ocorrencia]

        regiao = request.args.get('regiao')
        if regiao:
            df = df[df['regiao'] == regiao]

        ano = request.args.get('ano')
        if ano:
            df = df[df['ano'] == int(ano)]

        # Agrupar por município (top 15)
        dados_agrupados = df.groupby('municipio')['quantidade'].sum().sort_values(ascending=False).head(15)

        fig = px.bar(
            x=dados_agrupados.values,
            y=dados_agrupados.index,
            orientation='h',
            labels={'x': 'Quantidade', 'y': 'Município'},
            title='Top 15 Municípios com Mais Ocorrências',
            color=dados_agrupados.values,
            color_continuous_scale='Blues'
        )

        fig.update_layout(height=600)

        return jsonify({
            'success': True,
            'grafico': fig.to_json()
        })

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grafico/evolucao-temporal')
def grafico_evolucao_temporal():
    """Gráfico de evolução temporal"""
    try:
        df = get_data_from_db()

        # Aplicar filtros
        tipo_ocorrencia = request.args.get('tipo_ocorrencia')
        if tipo_ocorrencia:
            df = df[df['tipo_ocorrencia'] == tipo_ocorrencia]

        municipio = request.args.get('municipio')
        if municipio:
            df = df[df['municipio'] == municipio]

        regiao = request.args.get('regiao')
        if regiao:
            df = df[df['regiao'] == regiao]

        # Agrupar por ano
        dados_agrupados = df.groupby('ano')['quantidade'].sum().sort_index()

        fig = px.line(
            x=dados_agrupados.index,
            y=dados_agrupados.values,
            labels={'x': 'Ano', 'y': 'Quantidade de Ocorrências'},
            title='Evolução Temporal das Ocorrências',
            markers=True
        )

        fig.update_layout(height=400)

        return jsonify({
            'success': True,
            'grafico': fig.to_json()
        })

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/grafico/ocorrencias-por-regiao')
def grafico_ocorrencias_regiao():
    """Gráfico de pizza - ocorrências por região"""
    try:
        df = get_data_from_db()

        # Aplicar filtros
        tipo_ocorrencia = request.args.get('tipo_ocorrencia')
        if tipo_ocorrencia:
            df = df[df['tipo_ocorrencia'] == tipo_ocorrencia]

        ano = request.args.get('ano')
        if ano:
            df = df[df['ano'] == int(ano)]

        # Agrupar por região
        dados_agrupados = df.groupby('regiao')['quantidade'].sum()

        fig = px.pie(
            values=dados_agrupados.values,
            names=dados_agrupados.index,
            title='Distribuição de Ocorrências por Região',
            hole=0.3
        )

        fig.update_layout(height=500)

        return jsonify({
            'success': True,
            'grafico': fig.to_json()
        })

    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
