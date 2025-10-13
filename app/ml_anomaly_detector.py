"""
Machine Learning-based Anomaly Detection for Suspicious Activity
Uses Isolation Forest algorithm to detect anomalous password reset patterns
"""

import os
import logging
import pickle
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import numpy as np
from flask import current_app
import joblib

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """
    Machine Learning-based anomaly detector using Isolation Forest algorithm.
    
    The Isolation Forest algorithm is particularly effective for anomaly detection because:
    - It isolates anomalies instead of profiling normal points
    - Works well with high-dimensional data
    - Efficient with large datasets
    - No assumption about data distribution
    """
    
    def __init__(self):
        """Initialize the ML anomaly detector"""
        self.model = None
        self.scaler = None
        self.feature_names = [
            'hour_of_day',
            'day_of_week',
            'requests_last_hour',
            'requests_last_day',
            'unique_ips_last_hour',
            'unique_ips_last_day',
            'country_changes_last_day',
            'time_since_last_activity',
            'avg_time_between_requests',
            'is_known_country',
            'is_known_ip',
            'user_activity_count'
        ]
        self.model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'instance', 
            'ml_models', 
            'anomaly_detector.pkl'
        )
        self.scaler_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'instance', 
            'ml_models', 
            'feature_scaler.pkl'
        )
        self._ensure_model_directory()
        self._load_model()
    
    def _ensure_model_directory(self):
        """Ensure the ML models directory exists"""
        model_dir = os.path.dirname(self.model_path)
        os.makedirs(model_dir, exist_ok=True)
    
    def _load_model(self):
        """Load trained model and scaler from disk"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"✓ ML anomaly detection model loaded successfully")
            else:
                logger.warning("ML model not found. Run training script to create model.")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            self.model = None
            self.scaler = None
    
    def _save_model(self):
        """Save trained model and scaler to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"✓ ML model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving ML model: {e}")
    
    def extract_features(self, email: str, ip_address: str, user_id: Optional[int], 
                        country: Optional[str], db_session) -> Dict[str, float]:
        """
        Extract features from suspicious activity data for ML model.
        
        Args:
            email: User's email address
            ip_address: Current IP address
            user_id: User ID (optional)
            country: Current country (optional)
            db_session: Database session for queries
            
        Returns:
            Dictionary of features for ML model
        """
        from .models import SuspiciousActivity
        
        now = datetime.utcnow()
        features = {}
        
        # Time-based features
        features['hour_of_day'] = now.hour
        features['day_of_week'] = now.weekday()
        
        # Activity frequency features
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Count requests in last hour
        requests_last_hour = db_session.query(SuspiciousActivity).filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.timestamp >= one_hour_ago
        ).count()
        features['requests_last_hour'] = requests_last_hour
        
        # Count requests in last day
        requests_last_day = db_session.query(SuspiciousActivity).filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.timestamp >= one_day_ago
        ).count()
        features['requests_last_day'] = requests_last_day
        
        # Count unique IPs in last hour
        unique_ips_hour = db_session.query(
            db_session.query(SuspiciousActivity.ip_address).filter(
                SuspiciousActivity.email == email,
                SuspiciousActivity.timestamp >= one_hour_ago
            ).distinct().count()
        ).scalar() or 0
        features['unique_ips_last_hour'] = unique_ips_hour
        
        # Count unique IPs in last day
        unique_ips_day = db_session.query(
            db_session.query(SuspiciousActivity.ip_address).filter(
                SuspiciousActivity.email == email,
                SuspiciousActivity.timestamp >= one_day_ago
            ).distinct().count()
        ).scalar() or 0
        features['unique_ips_last_day'] = unique_ips_day
        
        # Count country changes in last day
        if country:
            country_changes = db_session.query(
                db_session.query(SuspiciousActivity.country).filter(
                    SuspiciousActivity.email == email,
                    SuspiciousActivity.timestamp >= one_day_ago,
                    SuspiciousActivity.country.isnot(None),
                    SuspiciousActivity.country != country
                ).distinct().count()
            ).scalar() or 0
            features['country_changes_last_day'] = country_changes
        else:
            features['country_changes_last_day'] = 0
        
        # Time since last activity
        last_activity = db_session.query(SuspiciousActivity).filter(
            SuspiciousActivity.email == email
        ).order_by(SuspiciousActivity.timestamp.desc()).first()
        
        if last_activity:
            time_diff = (now - last_activity.timestamp).total_seconds() / 3600  # hours
            features['time_since_last_activity'] = time_diff
        else:
            features['time_since_last_activity'] = 999  # New user, large value
        
        # Average time between requests (last 10 requests)
        recent_activities = db_session.query(SuspiciousActivity).filter(
            SuspiciousActivity.email == email
        ).order_by(SuspiciousActivity.timestamp.desc()).limit(10).all()
        
        if len(recent_activities) > 1:
            time_diffs = []
            for i in range(len(recent_activities) - 1):
                diff = (recent_activities[i].timestamp - recent_activities[i+1].timestamp).total_seconds() / 3600
                time_diffs.append(diff)
            features['avg_time_between_requests'] = np.mean(time_diffs) if time_diffs else 24
        else:
            features['avg_time_between_requests'] = 24  # Default to 1 day
        
        # Historical pattern features
        thirty_days_ago = now - timedelta(days=30)
        
        # Check if country is known (appeared in last 30 days)
        if country:
            known_country = db_session.query(SuspiciousActivity).filter(
                SuspiciousActivity.email == email,
                SuspiciousActivity.country == country,
                SuspiciousActivity.timestamp >= thirty_days_ago
            ).first()
            features['is_known_country'] = 1.0 if known_country else 0.0
        else:
            features['is_known_country'] = 0.0
        
        # Check if IP is known
        known_ip = db_session.query(SuspiciousActivity).filter(
            SuspiciousActivity.email == email,
            SuspiciousActivity.ip_address == ip_address,
            SuspiciousActivity.timestamp >= thirty_days_ago
        ).first()
        features['is_known_ip'] = 1.0 if known_ip else 0.0
        
        # Total user activity count
        if user_id:
            total_activity = db_session.query(SuspiciousActivity).filter(
                SuspiciousActivity.user_id == user_id
            ).count()
            features['user_activity_count'] = total_activity
        else:
            features['user_activity_count'] = 0
        
        return features
    
    def predict_anomaly(self, features: Dict[str, float]) -> Tuple[bool, float, str]:
        """
        Predict if the activity is anomalous using the trained ML model.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Tuple of (is_anomalous, anomaly_score, explanation)
        """
        if self.model is None or self.scaler is None:
            logger.warning("ML model not loaded. Skipping ML-based detection.")
            return False, 0.0, "ML model not available"
        
        try:
            # Ensure features are in correct order
            feature_vector = np.array([[features.get(name, 0) for name in self.feature_names]])
            
            # Scale features
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Predict anomaly score (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(feature_vector_scaled)[0]
            
            # Get anomaly score (lower = more anomalous)
            anomaly_score = self.model.score_samples(feature_vector_scaled)[0]
            
            # Convert to 0-1 scale (higher = more anomalous)
            # Typical Isolation Forest scores range from -0.5 to 0.5
            normalized_score = max(0, min(1, (-anomaly_score + 0.5)))
            
            is_anomalous = prediction == -1 or normalized_score > 0.7
            
            # Generate explanation based on features
            explanation = self._generate_explanation(features, normalized_score)
            
            logger.info(f"ML anomaly detection: score={normalized_score:.3f}, anomalous={is_anomalous}")
            
            return is_anomalous, normalized_score, explanation
            
        except Exception as e:
            logger.error(f"Error in ML anomaly prediction: {e}")
            return False, 0.0, f"Prediction error: {str(e)}"
    
    def _generate_explanation(self, features: Dict[str, float], score: float) -> str:
        """Generate human-readable explanation of anomaly detection"""
        explanations = []
        
        if score > 0.7:
            explanations.append(f"High anomaly score ({score:.2f})")
        
        if features.get('requests_last_hour', 0) > 3:
            explanations.append(f"{int(features['requests_last_hour'])} requests in last hour")
        
        if features.get('unique_ips_last_hour', 0) > 2:
            explanations.append(f"{int(features['unique_ips_last_hour'])} different IPs in last hour")
        
        if features.get('is_known_country', 1) == 0:
            explanations.append("Request from new country")
        
        if features.get('is_known_ip', 1) == 0:
            explanations.append("Request from new IP address")
        
        if features.get('time_since_last_activity', 999) < 0.25:  # Less than 15 minutes
            explanations.append("Very short time since last activity")
        
        unusual_hour = features.get('hour_of_day', 12)
        if unusual_hour < 6 or unusual_hour > 22:
            explanations.append(f"Unusual hour: {int(unusual_hour)}:00")
        
        if explanations:
            return "ML detected: " + "; ".join(explanations)
        else:
            return f"ML anomaly score: {score:.2f}"
    
    def train_model(self, db_session, contamination: float = 0.1):
        """
        Train the Isolation Forest model on historical suspicious activity data.
        
        Args:
            db_session: Database session
            contamination: Expected proportion of anomalies (default: 10%)
        """
        from .models import SuspiciousActivity
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        try:
            logger.info("Starting ML model training...")
            
            # Get all suspicious activities
            activities = db_session.query(SuspiciousActivity).all()
            
            if len(activities) < 100:
                logger.warning(f"Insufficient data for training (need 100+, got {len(activities)})")
                return False
            
            # Extract features for all activities
            feature_matrix = []
            for activity in activities:
                features = self.extract_features(
                    activity.email,
                    activity.ip_address,
                    activity.user_id,
                    activity.country,
                    db_session
                )
                feature_vector = [features.get(name, 0) for name in self.feature_names]
                feature_matrix.append(feature_vector)
            
            X = np.array(feature_matrix)
            
            logger.info(f"Training on {X.shape[0]} samples with {X.shape[1]} features")
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42,
                n_jobs=-1  # Use all CPU cores
            )
            
            self.model.fit(X_scaled)
            
            # Save model
            self._save_model()
            
            # Get training statistics
            predictions = self.model.predict(X_scaled)
            anomalies = np.sum(predictions == -1)
            
            logger.info(f"✓ Model training complete: {anomalies}/{len(predictions)} anomalies detected")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return False
    
    def evaluate_model(self, db_session) -> Dict[str, float]:
        """
        Evaluate the model's performance on current data.
        
        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None or self.scaler is None:
            return {"error": "Model not loaded"}
        
        from .models import SuspiciousActivity
        
        try:
            # Get recent activities
            activities = db_session.query(SuspiciousActivity).limit(1000).all()
            
            if not activities:
                return {"error": "No data available"}
            
            # Extract features
            feature_matrix = []
            known_anomalies = []
            
            for activity in activities:
                features = self.extract_features(
                    activity.email,
                    activity.ip_address,
                    activity.user_id,
                    activity.country,
                    db_session
                )
                feature_vector = [features.get(name, 0) for name in self.feature_names]
                feature_matrix.append(feature_vector)
                known_anomalies.append(1 if activity.alert_triggered else 0)
            
            X = np.array(feature_matrix)
            X_scaled = self.scaler.transform(X)
            
            # Get predictions
            predictions = self.model.predict(X_scaled)
            anomaly_predictions = (predictions == -1).astype(int)
            
            # Calculate metrics
            true_positives = np.sum((anomaly_predictions == 1) & (np.array(known_anomalies) == 1))
            false_positives = np.sum((anomaly_predictions == 1) & (np.array(known_anomalies) == 0))
            false_negatives = np.sum((anomaly_predictions == 0) & (np.array(known_anomalies) == 1))
            true_negatives = np.sum((anomaly_predictions == 0) & (np.array(known_anomalies) == 0))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                "samples_evaluated": len(activities),
                "anomalies_detected": int(np.sum(anomaly_predictions)),
                "known_alerts": int(np.sum(known_anomalies)),
                "true_positives": int(true_positives),
                "false_positives": int(false_positives),
                "false_negatives": int(false_negatives),
                "true_negatives": int(true_negatives),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1_score)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {"error": str(e)}


# Global instance
ml_detector = MLAnomalyDetector()
