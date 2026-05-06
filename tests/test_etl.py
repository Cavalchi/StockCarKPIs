import pytest
import pandas as pd
from stockcar_kpis.etl.load_db import (
    validar_corridas,
    validar_resultados,
    validar_pit_stops,
    ValidationError
)

def test_validar_corridas_sucesso():
    df = pd.DataFrame({
        "data": ["2024-03-03"],
        "circuito": ["Interlagos"],
        "condicoes_pista": ["Seco"]
    })
    # Não deve lançar erro
    validar_corridas(df, 2024)

def test_validar_corridas_colunas_faltando():
    df = pd.DataFrame({
        "data": ["2024-03-03"]
        # Falta circuito e condicoes_pista
    })
    with pytest.raises(ValidationError) as exc_info:
        validar_corridas(df, 2024)
    assert "colunas faltando" in str(exc_info.value)

def test_validar_resultados_posicao_duplicada():
    df = pd.DataFrame({
        "etapa": [1, 1],
        "piloto": ["Piloto A", "Piloto B"],
        "equipe": ["Eq A", "Eq B"],
        "posicao": [1, 1], # Empate na mesma corrida (invalido)
        "posicao_largada": [2, 3],
        "voltas": [30, 30]
    })
    with pytest.raises(ValidationError) as exc_info:
        validar_resultados(df, 2024, n_etapas=1)
    assert "posições duplicadas" in str(exc_info.value)

def test_validar_pit_stops_duracao_invalida():
    df = pd.DataFrame({
        "etapa": [1],
        "piloto": ["Piloto A"],
        "equipe": ["Eq A"],
        "volta": [15],
        "duracao_s": [-1.0] # Duração negativa (invalido)
    })
    with pytest.raises(ValidationError) as exc_info:
        validar_pit_stops(df, 2024, n_etapas=1)
    assert "duração <= 0" in str(exc_info.value)
