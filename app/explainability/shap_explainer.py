"""
shap_explainer.py
SHAP explainability module for multimodal model.
- Supports SHAP value computation for model predictions
- Modular and reusable
"""

import shap
import torch
from typing import Callable, Any, List

class SHAPExplainer:
    """
    Wrapper for SHAP explainability for PyTorch models.
    """
    def __init__(self, model: torch.nn.Module, masker: Callable, device: str = None):
        self.model = model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        self.masker = masker  # Function to mask input features for SHAP
        self.explainer = shap.Explainer(self._predict, masker)

    def _predict(self, inputs):
        """
        SHAP expects a function that takes numpy and returns model outputs.
        """
        with torch.no_grad():
            if isinstance(inputs, torch.Tensor):
                inputs = inputs.to(self.device)
            else:
                inputs = torch.tensor(inputs, dtype=torch.float32, device=self.device)
            outputs = self.model(inputs)
            if isinstance(outputs, tuple):
                outputs = outputs[0]
            return outputs.cpu().numpy()

    def shap_values(self, data: Any, **kwargs) -> List:
        """
        Compute SHAP values for the given data.
        """
        return self.explainer(data, **kwargs)

    def explain_prediction(self, data: Any, **kwargs) -> dict:
        """
        Returns SHAP values and base values for a prediction.
        """
        shap_values = self.shap_values(data, **kwargs)
        return {
            "shap_values": shap_values.values.tolist(),
            "base_values": shap_values.base_values.tolist(),
            "data": shap_values.data.tolist()
        }
