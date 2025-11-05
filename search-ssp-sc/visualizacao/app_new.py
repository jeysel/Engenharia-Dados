"""
Sistema de Visualização de Dados da SSP-SC - Nova Versão
Dashboard interativo com a nova estrutura de dados
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


def get_data_from_table(table_name: str, filtros: dict = None) -> pd.DataFrame:
    """
    Busca dados de uma tabela específica

    Args:
        table_name: Nome da tabela (roubo, furto, mortes_violentas, homicidio, violencia_domestica)
        filtros: Dicionário com filtros (ano, mes, municipio, regiao, etc)

    Returns:
        DataFrame com os dados
    """
    if not engine:
        logger.warning("Engine não disponível")
        return pd.DataFrame()

    try:
        query = f"SELECT * FROM {table_name}"
        conditions = []

        if filtros:
            if 'ano' in filtros and filtros['ano']:
                conditions.append(f"ano = {filtros['ano']}")
            if 'mes' in filtros and filtros['mes']:
                conditions.append(f"mes = {filtros['mes']}")
            if 'municipio' in filtros and filtros['municipio']:
                conditions.append(f"municipio = '{filtros['municipio']}'")
            if 'regiao' in filtros and filtros['regiao']:
                conditions.append(f"regiao = '{filtros['regiao']}'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY ano DESC, mes DESC"

        df = pd.read_sql(query, engine)
        logger.info(f"{len(df)} registros carregados da tabela {table_name}")
        return df

    except Exception as e:
        logger.error(f"Erro ao buscar dados de {table_name}: {e}")
        return pd.DataFrame()


def get_all_data(filtros: dict = None) -> pd.DataFrame:
    """
    Busca dados de todas as tabelas e combina

    Args:
        filtros: Filtros a aplicar

    Returns:
        DataFrame combinado
    """
    dfs = []

    # Buscar de cada tabela
    for tabela, categoria in [
        ('roubo', 'Roubo'),
        ('furto', 'Furto'),
        ('mortes_violentas', 'Mortes Violentas'),
        ('homicidio', 'Homicídio'),
        ('violencia_domestica', 'Violência Doméstica')
    ]:
        df = get_data_from_table(tabela, filtros)
        if not df.empty:
            df['categoria'] = categoria
            dfs.append(df)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()


@app.route('/')
def index():
    """Página principal"""
    return render_template('index_new.html')


@app.route('/api/dados')
def get_dados():
    """
    Endpoint para obter dados com filtros

    Query Parameters:
        - categoria: roubo, furto, mortes_violentas, homicidio, violencia_domestica
        - municipio: Filtrar por município
        - regiao: Filtrar por região
        - ano: Filtrar por ano
        - mes: Filtrar por mês
    """
    try:
        categoria = request.args.get('categoria', 'todas')
        filtros = {
            'ano': request.args.get('ano', type=int),
            'mes': request.args.get('mes', type=int),
            'municipio': request.args.get('municipio'),
            'regiao': request.args.get('regiao')
        }

        # Remover filtros None
        filtros = {k: v for k, v in filtros.items() if v is not None}

        if categoria == 'todas':
            df = get_all_data(filtros)
        else:
            df = get_data_from_table(categoria, filtros)

        # Converter para JSON
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
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filtros')
def get_filtros():
    """Endpoint para obter opções de filtros"""
    try:
        df = get_all_data()

        if df.empty:
            return jsonify({
                'success': True,
                'filtros': {
                    'categorias': [],
                    'municipios': [],
                    'regioes': [],
                    'anos': [],
                    'meses': []
                }
            })

        filtros = {
            'categorias': ['Roubo', 'Furto', 'Mortes Violentas', 'Homicídio', 'Violência Doméstica'],
            'municipios': sorted([m for m in df['municipio'].unique() if pd.notna(m)]),
            'regioes': sorted([r for r in df['regiao'].unique() if pd.notna(r)]),
            'anos': sorted([a for a in df['ano'].unique() if pd.notna(a)]),
            'meses': list(range(1, 13))
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
        categoria = request.args.get('categoria', 'todas')
        filtros = {
            'ano': request.args.get('ano', type=int),
            'mes': request.args.get('mes', type=int),
            'municipio': request.args.get('municipio'),
            'regiao': request.args.get('regiao')
        }

        filtros = {k: v for k, v in filtros.items() if v is not None}

        if categoria == 'todas':
            df = get_all_data(filtros)
        else:
            df = get_data_from_table(categoria, filtros)

        if df.empty:
            return jsonify({
                'success': True,
                'estatisticas': {
                    'total_ocorrencias': 0,
                    'total_registros': 0,
                    'municipios_afetados': 0,
                    'media_por_municipio': 0
                }
            })

        estatisticas = {
            'total_ocorrencias': int(df['quantidade'].sum()),
            'total_registros': len(df),
            'municipios_afetados': int(df['municipio'].nunique()),
            'media_por_municipio': float(df.groupby('municipio')['quantidade'].sum().mean()) if 'municipio' in df.columns else 0
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


@app.route('/api/grafico/ocorrencias-por-categoria')
def grafico_ocorrencias_categoria():
    """Gráfico de ocorrências por categoria"""
    try:
        filtros = {
            'ano': request.args.get('ano', type=int),
            'municipio': request.args.get('municipio'),
            'regiao': request.args.get('regiao')
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}

        df = get_all_data(filtros)

        if df.empty:
            return jsonify({'success': False, 'error': 'Sem dados disponíveis'}), 404

        # Agrupar por categoria
        dados_agrupados = df.groupby('categoria')['quantidade'].sum().sort_values(ascending=False)

        fig = px.bar(
            x=dados_agrupados.index,
            y=dados_agrupados.values,
            labels={'x': 'Categoria', 'y': 'Quantidade'},
            title='Ocorrências por Categoria',
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
        categoria = request.args.get('categoria', 'todas')
        filtros = {
            'ano': request.args.get('ano', type=int),
            'regiao': request.args.get('regiao')
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}

        if categoria == 'todas':
            df = get_all_data(filtros)
        else:
            df = get_data_from_table(categoria, filtros)

        if df.empty:
            return jsonify({'success': False, 'error': 'Sem dados disponíveis'}), 404

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
        categoria = request.args.get('categoria', 'todas')
        filtros = {
            'municipio': request.args.get('municipio'),
            'regiao': request.args.get('regiao')
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}

        if categoria == 'todas':
            df = get_all_data(filtros)
        else:
            df = get_data_from_table(categoria, filtros)

        if df.empty:
            return jsonify({'success': False, 'error': 'Sem dados disponíveis'}), 404

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


@app.route('/api/grafico/comparativo-categorias')
def grafico_comparativo_categorias():
    """Gráfico comparativo entre categorias ao longo do tempo"""
    try:
        filtros = {
            'municipio': request.args.get('municipio'),
            'regiao': request.args.get('regiao')
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}

        df = get_all_data(filtros)

        if df.empty:
            return jsonify({'success': False, 'error': 'Sem dados disponíveis'}), 404

        # Agrupar por ano e categoria
        dados_agrupados = df.groupby(['ano', 'categoria'])['quantidade'].sum().reset_index()

        fig = px.line(
            dados_agrupados,
            x='ano',
            y='quantidade',
            color='categoria',
            labels={'ano': 'Ano', 'quantidade': 'Quantidade', 'categoria': 'Categoria'},
            title='Comparativo de Categorias ao Longo do Tempo',
            markers=True
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


@app.route('/api/historico')
def get_historico():
    """Endpoint para obter histórico de execuções"""
    try:
        query = """
        SELECT
            id,
            data_hora_inicio,
            data_hora_fim,
            status,
            tipo_dados,
            fonte,
            registros_inseridos,
            registros_atualizados,
            registros_ignorados,
            anos_processados,
            mensagem
        FROM historico_execucao
        ORDER BY data_hora_inicio DESC
        LIMIT 50
        """

        df = pd.read_sql(query, engine)
        df = df.where(pd.notna(df), None)
        historico = df.to_dict('records')

        # Converter datetime para string
        for item in historico:
            if item.get('data_hora_inicio') and isinstance(item['data_hora_inicio'], datetime):
                item['data_hora_inicio'] = item['data_hora_inicio'].isoformat()
            if item.get('data_hora_fim') and isinstance(item['data_hora_fim'], datetime):
                item['data_hora_fim'] = item['data_hora_fim'].isoformat()

        return jsonify({
            'success': True,
            'total': len(historico),
            'historico': historico
        })

    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
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
