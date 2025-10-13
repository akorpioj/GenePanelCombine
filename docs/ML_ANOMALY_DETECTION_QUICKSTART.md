# ML-Based Anomaly Detection Quick Start

## Overview

This feature adds machine learning-based anomaly detection to the password reset security system using Isolation Forest algorithm.

## Installation

Dependencies are already in `requirements.txt`. Install them:

```bash
pip install -r requirements.txt
```

This includes:
- `scikit-learn>=1.3.0` - ML framework
- `joblib>=1.3.0` - Model serialization

## Quick Start

### 1. Collect Data

The ML model needs suspicious activity data to train on. Use the application normally and let it collect password reset activity:

- Minimum: 100 activities
- Recommended: 1000+ activities
- Better with diverse patterns (normal and suspicious)

Check current data count:
```sql
SELECT COUNT(*) FROM suspicious_activity;
```

### 2. Train the Model

Once you have enough data:

```bash
python scripts/train_anomaly_detector.py
```

This will:
- Extract features from all suspicious activities
- Train an Isolation Forest model
- Evaluate performance
- Save model to `instance/ml_models/`

### 3. Enable ML Detection

In your `.env` file:

```bash
ML_ANOMALY_DETECTION_ENABLED=True
```

### 4. Monitor Performance

Check logs for ML detection results:
```
INFO: ML anomaly detection: score=0.823, anomalous=True
```

## Training Options

### Basic Training
```bash
python scripts/train_anomaly_detector.py
```

### Adjust Sensitivity
```bash
# More conservative (fewer false positives)
python scripts/train_anomaly_detector.py --contamination 0.05

# More sensitive (catch more anomalies)
python scripts/train_anomaly_detector.py --contamination 0.15
```

### Skip Evaluation
```bash
python scripts/train_anomaly_detector.py --no-eval
```

## Understanding Performance Metrics

After training, you'll see metrics like:

```
Performance Metrics:
  Precision: 0.735  # 73.5% of ML alerts are real
  Recall:    0.847  # Catches 84.7% of real alerts
  F1 Score:  0.787  # Overall performance
```

**Good Performance:**
- Precision > 0.7 (not too many false positives)
- Recall > 0.7 (not missing too many real alerts)
- F1 Score > 0.7 (good balance)

**If performance is poor:**
1. Collect more training data
2. Adjust contamination parameter
3. Wait for more diverse activity patterns

## Features Analyzed

The ML model analyzes 12 features:

**Temporal**: Hour of day, day of week, time since last activity
**Frequency**: Requests per hour/day, unique IPs per hour/day
**Geographic**: New countries, new IPs, country changes
**Behavioral**: Average time between requests, total user activity

## Maintenance

### Retraining Schedule

Retrain the model regularly to adapt to changing patterns:

**Weekly (Recommended for high-traffic sites):**
```bash
# Add to cron (Linux/Mac)
0 3 * * 0 cd /path/to/app && python scripts/train_anomaly_detector.py

# Or Windows Task Scheduler
```

**Monthly (For lower-traffic sites):**
```bash
0 3 1 * * cd /path/to/app && python scripts/train_anomaly_detector.py
```

### Model Backup

Before retraining, backup the current model:

```bash
cp instance/ml_models/anomaly_detector.pkl instance/ml_models/anomaly_detector_backup.pkl
cp instance/ml_models/feature_scaler.pkl instance/ml_models/feature_scaler_backup.pkl
```

## Integration

The ML detection integrates seamlessly with existing rule-based detection:

1. **Password reset requested**
2. **Rule-based checks run** (multiple attempts, geographic anomaly, time pattern)
3. **ML model checks** (if enabled and available)
4. **Combined result**: Alert if ANY detector triggers
5. **Admin notified** with all detection reasons

## Troubleshooting

### "ML model not found"
**Solution:** Train the model first:
```bash
python scripts/train_anomaly_detector.py
```

### "Insufficient data for training"
**Need:** At least 100 suspicious activity records
**Solution:** Wait for more password reset activity or use application more

### High false positive rate
**Solution:** Decrease contamination:
```bash
python scripts/train_anomaly_detector.py --contamination 0.05
```

### Missing real attacks
**Solution:** Increase contamination:
```bash
python scripts/train_anomaly_detector.py --contamination 0.15
```

### Import errors
**Solution:** Install dependencies:
```bash
pip install scikit-learn joblib
```

## Configuration

### Environment Variables

```bash
# Enable/disable ML detection
ML_ANOMALY_DETECTION_ENABLED=False  # Default: False

# Expected proportion of anomalies (0.05-0.15)
ML_ANOMALY_CONTAMINATION=0.1  # Default: 0.1 (10%)
```

### File Locations

- **Model file**: `instance/ml_models/anomaly_detector.pkl`
- **Scaler file**: `instance/ml_models/feature_scaler.pkl`
- **Training script**: `scripts/train_anomaly_detector.py`
- **ML detector module**: `app/ml_anomaly_detector.py`

## Example Workflow

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Use application, collect data (wait for 100+ activities)

# 3. Train model
python scripts/train_anomaly_detector.py

# 4. Review performance metrics
# If F1 score > 0.7, proceed. Otherwise adjust contamination.

# 5. Enable ML detection
echo "ML_ANOMALY_DETECTION_ENABLED=True" >> .env

# 6. Restart application
python run.py

# 7. Monitor logs for ML detection results

# 8. Setup weekly retraining (cron or task scheduler)
```

## Benefits

- **Adaptive**: Learns YOUR specific user patterns
- **Subtle Detection**: Catches patterns rules might miss
- **Improves Over Time**: Gets better with more data
- **Automatic**: No need to write new rules
- **Combines Signals**: Uses multiple weak indicators together

## Limitations

- **Training Data Required**: Needs 100+ activities minimum
- **Periodic Retraining**: Patterns change over time
- **Complementary**: Works best alongside rule-based detection
- **Not Real-time Learning**: Requires explicit retraining
- **False Positives**: May flag unusual but legitimate activity

## Performance

- **Training Time**: ~1-5 seconds for 1000 samples
- **Prediction Time**: <1ms per request
- **Model Size**: 100KB - 1MB
- **Memory Usage**: Minimal (~5MB in memory)
- **CPU Usage**: Negligible during prediction

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in application
3. See full documentation: `docs/SUSPICIOUS_ACTIVITY_DETECTION.md`

## Version

ML Anomaly Detection v1.0
- Algorithm: Isolation Forest
- Features: 12 engineered features
- Framework: scikit-learn 1.3+
