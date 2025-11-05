"""
Modelos de banco de dados para SSP-SC
Define as novas tabelas conforme especificação
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Roubo(Base):
    """Tabela para armazenar dados de roubo"""
    __tablename__ = 'roubo'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=True)
    municipio = Column(String(200))
    regiao = Column(String(100))
    tipo_roubo = Column(String(200))  # Ex: roubo a mão armada, roubo de veículo, etc
    quantidade = Column(Integer, default=0)
    fonte = Column(String(500))  # URL ou nome do arquivo PDF/CSV origem
    data_coleta = Column(DateTime, default=datetime.now)
    dados_brutos = Column(Text)  # JSON com dados originais

    __table_args__ = (
        Index('idx_roubo_ano_mes', 'ano', 'mes'),
        Index('idx_roubo_municipio', 'municipio'),
    )


class Furto(Base):
    """Tabela para armazenar dados de furto"""
    __tablename__ = 'furto'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=True)
    municipio = Column(String(200))
    regiao = Column(String(100))
    tipo_furto = Column(String(200))  # Ex: furto simples, furto qualificado, etc
    quantidade = Column(Integer, default=0)
    fonte = Column(String(500))
    data_coleta = Column(DateTime, default=datetime.now)
    dados_brutos = Column(Text)

    __table_args__ = (
        Index('idx_furto_ano_mes', 'ano', 'mes'),
        Index('idx_furto_municipio', 'municipio'),
    )


class MortesViolentas(Base):
    """Tabela para armazenar dados de mortes violentas"""
    __tablename__ = 'mortes_violentas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=True)
    municipio = Column(String(200))
    regiao = Column(String(100))
    tipo_morte = Column(String(200))  # Ex: homicídio doloso, latrocínio, etc
    quantidade = Column(Integer, default=0)
    fonte = Column(String(500))
    data_coleta = Column(DateTime, default=datetime.now)
    dados_brutos = Column(Text)

    __table_args__ = (
        Index('idx_mortes_ano_mes', 'ano', 'mes'),
        Index('idx_mortes_municipio', 'municipio'),
    )


class Homicidio(Base):
    """Tabela para armazenar dados específicos de homicídio"""
    __tablename__ = 'homicidio'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=True)
    municipio = Column(String(200))
    regiao = Column(String(100))
    tipo_homicidio = Column(String(200))  # Ex: doloso, culposo, feminicídio, etc
    quantidade = Column(Integer, default=0)
    fonte = Column(String(500))
    data_coleta = Column(DateTime, default=datetime.now)
    dados_brutos = Column(Text)

    __table_args__ = (
        Index('idx_homicidio_ano_mes', 'ano', 'mes'),
        Index('idx_homicidio_municipio', 'municipio'),
    )


class ViolenciaDomestica(Base):
    """Tabela para armazenar dados de violência doméstica"""
    __tablename__ = 'violencia_domestica'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False)
    semestre = Column(Integer, nullable=True)  # 1 ou 2
    mes = Column(Integer, nullable=True)
    municipio = Column(String(200))
    regiao = Column(String(100))
    tipo_registro = Column(String(100))  # 'instaurado' ou 'remetido'
    tipo_violencia = Column(String(200))  # Ex: física, psicológica, etc
    quantidade = Column(Integer, default=0)
    fonte = Column(String(500))
    data_coleta = Column(DateTime, default=datetime.now)
    dados_brutos = Column(Text)

    __table_args__ = (
        Index('idx_violencia_ano_semestre', 'ano', 'semestre'),
        Index('idx_violencia_municipio', 'municipio'),
        Index('idx_violencia_tipo_registro', 'tipo_registro'),
    )


class HistoricoExecucao(Base):
    """Tabela para registrar histórico de execuções do extrator"""
    __tablename__ = 'historico_execucao'

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_hora_inicio = Column(DateTime, default=datetime.now, nullable=False)
    data_hora_fim = Column(DateTime)
    status = Column(String(50))  # 'sucesso', 'erro', 'parcial'
    tipo_dados = Column(String(100))  # 'roubo', 'furto', 'mortes_violentas', etc
    fonte = Column(String(500))  # URL ou arquivo processado
    registros_inseridos = Column(Integer, default=0)
    registros_atualizados = Column(Integer, default=0)
    registros_ignorados = Column(Integer, default=0)
    anos_processados = Column(String(200))  # Ex: "2023,2024,2025"
    mensagem = Column(Text)  # Mensagens de log ou erros
    detalhes = Column(Text)  # JSON com detalhes adicionais

    __table_args__ = (
        Index('idx_historico_data', 'data_hora_inicio'),
        Index('idx_historico_tipo', 'tipo_dados'),
    )
