from sklearn.ensemble import IsolationForest
import numpy as np

class HealthMonitor:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1)
        self.is_trained = False
    
    def train_model(self, data: np.ndarray):
        self.model.fit(data)
        self.is_trained = True
    
    def detect_anomalies(self, new_data: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Model not trained")
        return self.model.predict(new_data)