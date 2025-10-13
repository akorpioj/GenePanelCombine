"""
Train or retrain the ML-based anomaly detection model
Run this script periodically (e.g., weekly) to keep the model updated with new patterns
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.ml_anomaly_detector import ml_detector
from app.models import SuspiciousActivity

def train_model(contamination=0.1, evaluate=True):
    """
    Train the ML anomaly detection model.
    
    Args:
        contamination: Expected proportion of anomalies (0.05 = 5%, 0.1 = 10%)
        evaluate: Whether to evaluate the model after training
    """
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("ML Anomaly Detection Model Training")
        print("="*60)
        
        # Check data availability
        total_activities = SuspiciousActivity.query.count()
        alert_activities = SuspiciousActivity.query.filter_by(alert_triggered=True).count()
        
        print(f"\nData Statistics:")
        print(f"  Total activities: {total_activities}")
        print(f"  Alert activities: {alert_activities}")
        print(f"  Alert rate: {alert_activities/total_activities*100:.1f}%" if total_activities > 0 else "  Alert rate: N/A")
        
        if total_activities < 100:
            print(f"\n⚠️  Warning: Insufficient data for training")
            print(f"   Need at least 100 activities, got {total_activities}")
            print(f"   Model training skipped.")
            return False
        
        print(f"\nContamination parameter: {contamination*100:.1f}%")
        print(f"(Expected proportion of anomalies in training data)\n")
        
        # Train the model
        print("Training model...")
        success = ml_detector.train_model(db.session, contamination=contamination)
        
        if not success:
            print("\n❌ Model training failed")
            return False
        
        print("\n✓ Model training completed successfully")
        
        # Evaluate the model
        if evaluate:
            print("\nEvaluating model performance...")
            metrics = ml_detector.evaluate_model(db.session)
            
            if "error" in metrics:
                print(f"⚠️  Evaluation error: {metrics['error']}")
            else:
                print(f"\nEvaluation Results:")
                print(f"  Samples evaluated: {metrics['samples_evaluated']}")
                print(f"  Anomalies detected: {metrics['anomalies_detected']}")
                print(f"  Known alerts: {metrics['known_alerts']}")
                print(f"\nConfusion Matrix:")
                print(f"  True Positives:  {metrics['true_positives']}")
                print(f"  False Positives: {metrics['false_positives']}")
                print(f"  True Negatives:  {metrics['true_negatives']}")
                print(f"  False Negatives: {metrics['false_negatives']}")
                print(f"\nPerformance Metrics:")
                print(f"  Precision: {metrics['precision']:.3f}")
                print(f"  Recall:    {metrics['recall']:.3f}")
                print(f"  F1 Score:  {metrics['f1_score']:.3f}")
                
                # Interpretation
                print(f"\nInterpretation:")
                if metrics['precision'] > 0.7:
                    print(f"  ✓ Good precision: {metrics['precision']*100:.1f}% of detected anomalies are real alerts")
                else:
                    print(f"  ⚠️  Low precision: Many false positives detected")
                
                if metrics['recall'] > 0.7:
                    print(f"  ✓ Good recall: {metrics['recall']*100:.1f}% of real alerts are detected")
                else:
                    print(f"  ⚠️  Low recall: Many real alerts are missed")
                
                if metrics['f1_score'] > 0.7:
                    print(f"  ✓ Good overall performance (F1: {metrics['f1_score']:.3f})")
                else:
                    print(f"  ⚠️  Consider adjusting contamination parameter")
        
        print(f"\n{'='*60}")
        print("Training complete!")
        print("="*60)
        
        return True


def main():
    """Main entry point for training script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML anomaly detection model')
    parser.add_argument(
        '--contamination',
        type=float,
        default=0.1,
        help='Expected proportion of anomalies (default: 0.1 = 10%%)'
    )
    parser.add_argument(
        '--no-eval',
        action='store_true',
        help='Skip model evaluation after training'
    )
    
    args = parser.parse_args()
    
    # Validate contamination parameter
    if args.contamination <= 0 or args.contamination >= 0.5:
        print("Error: contamination must be between 0 and 0.5")
        sys.exit(1)
    
    success = train_model(
        contamination=args.contamination,
        evaluate=not args.no_eval
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
