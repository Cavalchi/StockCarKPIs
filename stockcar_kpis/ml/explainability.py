"""
ml/explainability.py
Módulo de explicabilidade para o modelo de Machine Learning
Usa SHAP values para mostrar por que o modelo fez uma previsão
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from typing import Tuple, Dict, List
import warnings

warnings.filterwarnings("ignore")


class ModelExplainer:
    """
    Classe para explicar previsões de modelos de ML usando SHAP values.
    Mostra quais features foram mais importantes para a previsão.
    """

    def __init__(self, model: RandomForestRegressor, X_train: pd.DataFrame):
        """
        Inicializa o explainer.

        Args:
            model: Modelo RandomForest treinado
            X_train: DataFrame de treino (para calcular baseline)
        """
        self.model = model
        self.X_train = X_train
        self.feature_names = X_train.columns.tolist()
        self.baseline = X_train.mean().values

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """
        Retorna as features mais importantes do modelo.

        Args:
            top_n: Número de features a retornar

        Returns:
            DataFrame com features e importância
        """
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]

        return pd.DataFrame({
            "feature": [self.feature_names[i] for i in indices],
            "importance": importances[indices],
            "importance_pct": (importances[indices] * 100).round(2)
        })

    def explain_prediction(self, X_sample: pd.DataFrame) -> Dict:
        """
        Explica uma previsão individual usando aproximação de SHAP.

        Args:
            X_sample: DataFrame com 1 linha (amostra a explicar)

        Returns:
            Dict com explicação da previsão
        """
        if len(X_sample) != 1:
            raise ValueError("X_sample deve ter exatamente 1 linha")

        prediction = self.model.predict(X_sample)[0]
        sample_values = X_sample.iloc[0].values

        contributions = []
        for i, feature_name in enumerate(self.feature_names):
            X_baseline = X_sample.copy()
            X_baseline.iloc[0, i] = self.baseline[i]
            pred_baseline = self.model.predict(X_baseline)[0]
            contribution = prediction - pred_baseline

            contributions.append({
                "feature": feature_name,
                "value": sample_values[i],
                "contribution": contribution,
                "direction": "↑" if contribution > 0 else "↓"
            })

        contributions = sorted(
            contributions,
            key=lambda x: abs(x["contribution"]),
            reverse=True
        )

        return {
            "prediction": prediction,
            "contributions": contributions[:5],
            "mae_estimate": self._estimate_mae()
        }

    def _estimate_mae(self) -> float:
        """Estima o MAE do modelo no conjunto de treino."""
        from sklearn.metrics import mean_absolute_error
        y_pred = self.model.predict(self.X_train)
        # Nota: em produção, usar conjunto de validação separado
        return float(np.mean(np.abs(self.X_train.index - y_pred)))

    def get_prediction_narrative(self, X_sample: pd.DataFrame) -> str:
        """
        Gera uma narrativa em português explicando a previsão.

        Args:
            X_sample: DataFrame com 1 linha

        Returns:
            String com explicação em linguagem natural
        """
        explanation = self.explain_prediction(X_sample)
        prediction = explanation["prediction"]
        contributions = explanation["contributions"]

        narrative = f"**Previsão: Posição Final P{int(round(prediction))}**\n\n"
        narrative += "Com base no histórico da Stock Car e nas características da sua entrada:\n\n"

        feature_names_pt = {
            "posicao_largada": "Posição de Largada",
            "Eurofarma RC": "Equipe: Eurofarma RC",
            "Ipiranga Racing": "Equipe: Ipiranga Racing",
            "RCM Motorsport": "Equipe: RCM Motorsport",
            "Full Time Sports": "Equipe: Full Time Sports",
        }

        for i, contrib in enumerate(contributions, 1):
            feature = contrib["feature"]
            direction = contrib["direction"]
            impact = abs(contrib["contribution"])
            feature_display = feature_names_pt.get(feature, feature.replace("equipe_", "Eq: "))
            narrative += f"**{i}. {feature_display}** {direction} (impacto: {impact:+.2f} pos)\n"

        return narrative


def create_prediction_explanation_chart(explanation: Dict) -> str:
    """
    Cria um gráfico HTML mostrando a explicação da previsão.

    Args:
        explanation: Dict retornado por explain_prediction()

    Returns:
        String HTML com gráfico
    """
    contributions = explanation["contributions"]

    features = [c["feature"].replace("equipe_", "Eq: ") for c in contributions]
    values = [c["contribution"] for c in contributions]
    colors = ["#00FF41" if v > 0 else "#FF0080" for v in values]

    max_abs = max(abs(v) for v in values) if values else 1
    html = """
    <div style="background-color: #1A1F3A; padding: 20px; border-radius: 8px;
                border: 1px solid rgba(0,217,255,0.2);">
        <h4 style="color: #00D9FF; margin-top: 0; text-transform: uppercase;
                   letter-spacing: 1px;">🔍 Top Fatores na Previsão</h4>
        <div style="display: flex; flex-direction: column; gap: 12px;">
    """

    for feature, value, color in zip(features, values, colors):
        bar_width = max(5, int(abs(value) / max_abs * 200))
        direction = "▲" if value > 0 else "▼"
        label = "Piora posição" if value > 0 else "Melhora posição"
        html += f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #888; width: 160px; font-size: 0.85em;
                         font-family: monospace; white-space: nowrap;
                         overflow: hidden; text-overflow: ellipsis;"
                  title="{feature}">{feature}</span>
            <div style="background-color: {color}; width: {bar_width}px;
                        height: 18px; border-radius: 3px; opacity: 0.75;
                        min-width: 4px;"></div>
            <span style="color: {color}; font-weight: bold; font-size: 0.9em;">
                {direction} {value:+.2f} <small style="opacity:0.6">({label})</small>
            </span>
        </div>
        """

    html += """
        </div>
    </div>
    """
    return html


if __name__ == "__main__":
    X_train = pd.DataFrame({
        "posicao_largada": np.random.randint(1, 35, 100),
        "Eurofarma RC": np.random.randint(0, 2, 100),
        "Ipiranga Racing": np.random.randint(0, 2, 100),
    })
    y_train = X_train["posicao_largada"] + np.random.normal(0, 2, 100)

    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    explainer = ModelExplainer(model, X_train)

    X_test = pd.DataFrame({
        "posicao_largada": [5],
        "Eurofarma RC": [1],
        "Ipiranga Racing": [0],
    })

    explanation = explainer.explain_prediction(X_test)
    print("Previsão:", explanation["prediction"])
    print("Contribuições:", explanation["contributions"])
    print(create_prediction_explanation_chart(explanation))
