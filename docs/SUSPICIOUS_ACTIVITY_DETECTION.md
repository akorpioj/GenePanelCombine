# Suspicious Activity Detection System

## Overview

The Suspicious Activity Detection System provides real-time monitoring and alerting for suspicious password reset patterns. It helps protect user accounts from unauthorized access attempts by detecting and alerting on anomalous behavior.

## Features

### 1. **Pattern Detection Algorithms**

The system implements both rule-based and machine learning-based detection:

#### Rule-Based Detection (3 algorithms)

#### Multiple Attempts Detection
- **Purpose**: Detect rapid password reset attempts from multiple IP addresses
- **Default Threshold**: 5 attempts within 1 hour
- **Trigger**: When the same email has X password reset requests from different IP addresses within Y hours
- **Configuration**: `SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD` and `SUSPICIOUS_ACTIVITY_TIME_WINDOW`

#### Geographic Anomaly Detection
- **Purpose**: Detect password reset attempts from unusual locations
- **Analysis Period**: 30-day historical pattern
- **Trigger**: When a password reset is requested from a new country AND new IP address
- **Data Source**: ip-api.com (free tier, 45 requests/minute)

#### Time Pattern Anomaly Detection
- **Purpose**: Detect password reset attempts at unusual times
- **Analysis Period**: 90-day activity pattern
- **Trigger**: When current request hour deviates by 6+ hours from historical activity patterns
- **Example**: If user typically resets passwords during business hours (9am-5pm), a 3am request triggers an alert

#### Machine Learning-Based Detection (Optional)

**Algorithm**: Isolation Forest

- **Purpose**: Learn complex patterns and detect anomalies automatically
- **Training Data**: Historical suspicious activity records (minimum 100 samples)
- **Features**: 12 engineered features including:
  - Temporal patterns (hour of day, day of week, time since last activity)
  - Request frequency (requests per hour/day, unique IPs)
  - Geographic patterns (known countries, known IPs, country changes)
  - User behavior (average time between requests, total activity count)
- **Output**: Anomaly score (0-1, higher = more anomalous) and human-readable explanation
- **Advantages**: 
  - Adapts to your specific user patterns
  - Detects subtle anomalies missed by rules
  - Improves over time with more data
  - Combines multiple weak signals

**How It Works:**

1. **Feature Extraction**: Extracts 12 behavioral and contextual features from current activity
2. **Anomaly Scoring**: Model assigns anomaly score based on how different the activity is from normal patterns
3. **Threshold Detection**: Activities with score > 0.7 or prediction = -1 are flagged as anomalous
4. **Explanation Generation**: Provides reasons like "Request from new country; 5 requests in last hour; Unusual hour: 3:00"

**Training Requirements:**
- Minimum 100 historical activities for training
- Recommended 1000+ activities for best performance
- Retrain weekly or monthly to capture new patterns
- Contamination parameter (default 10%) indicates expected anomaly rate

### 2. **Automatic Alerting**

When suspicious patterns are detected:
- **Admin Notifications**: All administrators receive detailed email alerts
- **Activity Logging**: Full details recorded in database
- **Audit Trail**: Integration with existing audit system
- **Alert Details Include**:
  - User information (username, email)
  - Activity details (IP address, location, timestamp)
  - Detected pattern reasons
  - Recommended actions

### 3. **Admin Dashboard**

Comprehensive monitoring interface at `/auth/admin/suspicious-activity`:

**Statistics**
- Total activities tracked
- Number of alerts triggered
- Unique IP addresses seen

**Filtering Options**
- Filter by email address
- Filter by IP address
- Show alerts only
- Pagination support (50 records per page)

**Activity Display**
- Timestamp of activity
- User email
- Activity type (request/success)
- Geographic location
- IP address
- Alert status and reasons

## Database Schema

### SuspiciousActivity Table

```sql
CREATE TABLE suspicious_activity (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,  -- Foreign key to users table
    email VARCHAR(255) NOT NULL,  -- Indexed for fast lookups
    activity_type VARCHAR(50) NOT NULL,  -- 'reset_request' or 'reset_success'
    ip_address VARCHAR(45) NOT NULL,  -- Indexed, supports IPv6
    country VARCHAR(100),
    city VARCHAR(100),
    user_agent VARCHAR(500),
    timestamp DATETIME NOT NULL,  -- Indexed for time-based queries
    alert_triggered BOOLEAN DEFAULT FALSE,
    alert_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Indexes:**
- `ix_suspicious_activity_email` - Fast email lookups
- `ix_suspicious_activity_ip_address` - Fast IP lookups
- `ix_suspicious_activity_timestamp` - Fast time-range queries

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Suspicious Activity Detection
SUSPICIOUS_ACTIVITY_ENABLED=True
SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD=5  # Attempts before alert
SUSPICIOUS_ACTIVITY_TIME_WINDOW=1  # Hours for multiple attempt detection
SUSPICIOUS_ACTIVITY_RETENTION_DAYS=90  # Days to keep records

# ML-based Anomaly Detection (Optional)
ML_ANOMALY_DETECTION_ENABLED=False  # Enable after training model
ML_ANOMALY_CONTAMINATION=0.1  # Expected proportion of anomalies (0.05-0.15)
```

### Configuration Options

**SUSPICIOUS_ACTIVITY_ENABLED**
- Type: Boolean
- Default: `True`
- Description: Master switch for suspicious activity detection

**SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD**
- Type: Integer
- Default: `5`
- Description: Number of password reset attempts from different IPs before triggering alert
- Range: 3-10 recommended

**SUSPICIOUS_ACTIVITY_TIME_WINDOW**
- Type: Integer
- Default: `1`
- Description: Time window in hours for multiple attempt detection
- Range: 0.5-2 hours recommended

**SUSPICIOUS_ACTIVITY_RETENTION_DAYS**
- Type: Integer
- Default: `90`
- Description: Number of days to keep suspicious activity records
- Note: Affects geographic and time pattern analysis accuracy

**ML_ANOMALY_DETECTION_ENABLED**
- Type: Boolean
- Default: `False`
- Description: Enable ML-based anomaly detection (requires trained model)
- Note: Must train model first using `scripts/train_anomaly_detector.py`

**ML_ANOMALY_CONTAMINATION**
- Type: Float
- Default: `0.1` (10%)
- Description: Expected proportion of anomalies in training data
- Range: 0.05-0.15 recommended (5%-15%)
- Note: Higher values make model more sensitive (more false positives)

## Integration Points

### 1. Password Reset Request Route

Location: `app/auth/routes.py` - `forgot_password()`

**Implementation:**
```python
from ..suspicious_activity_utils import get_client_ip, get_ip_geolocation
from ..models import SuspiciousActivity

# Get client information
ip_address = get_client_ip(request)
user_agent = request.headers.get('User-Agent', '')[:500]
geo_data = get_ip_geolocation(ip_address)

# Log activity
activity = SuspiciousActivity.log_activity(
    email=email,
    activity_type='reset_request',
    ip_address=ip_address,
    user_agent=user_agent,
    user_id=user.id,
    country=geo_data.get('country'),
    city=geo_data.get('city')
)

# Check for suspicious patterns
detection_result = SuspiciousActivity.check_all_patterns(
    email=email,
    ip_address=ip_address,
    user_id=user.id,
    country=geo_data.get('country')
)

# If suspicious, alert admins
if detection_result['is_suspicious']:
    activity.alert_triggered = True
    activity.alert_reason = '; '.join(detection_result['reasons'])
    db.session.commit()
    
    # Send admin alerts
    admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
    for admin in admin_users:
        email_service.send_suspicious_activity_alert(...)
```

### 2. Password Reset Success Route

Location: `app/auth/routes.py` - `reset_password()`

**Implementation:**
```python
# Log successful password reset
SuspiciousActivity.log_activity(
    email=user.email,
    activity_type='reset_success',
    ip_address=ip_address,
    user_agent=user_agent,
    user_id=user.id,
    country=geo_data.get('country'),
    city=geo_data.get('city')
)
```

## Helper Utilities

### Location: `app/suspicious_activity_utils.py`

#### get_client_ip(request)
Extracts the real client IP address from the request, handling proxies and load balancers.

**Priority Order:**
1. `X-Forwarded-For` header (first IP if multiple)
2. `X-Real-IP` header
3. `request.remote_addr`
4. Fallback: `'127.0.0.1'`

#### get_ip_geolocation(ip_address)
Retrieves geographic information for an IP address using ip-api.com.

**Features:**
- Free service (45 requests/minute limit)
- 2-second timeout to avoid request delays
- Handles localhost/private IPs gracefully
- Returns `{'country': str, 'city': str}` or `{None, None}` on failure

**Example Response:**
```python
{
    'country': 'United States',
    'city': 'New York'
}
```

## Email Notifications

### Suspicious Activity Alert

**Recipient**: Administrators
**Trigger**: When suspicious patterns are detected
**Template**: HTML and plain text versions

**Email Contains:**
- Alert header with warning emoji
- User details (username, email)
- Activity details (IP, location, timestamp)
- List of suspicious patterns detected
- Recommended actions:
  1. Review user's recent activity logs
  2. Contact user to verify requests
  3. Consider locking account if malicious
  4. Monitor for continued patterns
- Link to admin dashboard

**Example Subject:**
```
⚠️ Suspicious Password Reset Activity Detected - john_doe
```

## Admin Dashboard Usage

### Accessing the Dashboard

1. Log in as an administrator
2. Navigate to `/auth/admin/suspicious-activity`
3. Or use the admin navigation: **Suspicious Activity** tab

### Filtering Activities

**By Email:**
- Enter partial or complete email address
- Case-insensitive search
- Example: `john` matches `john@example.com`

**By IP Address:**
- Enter partial or complete IP
- Example: `192.168` matches all IPs starting with `192.168`

**Alerts Only:**
- Toggle to show only activities that triggered alerts
- Useful for focusing on high-priority items

### Understanding the Activity Table

**Color Coding:**
- White background: Normal activity
- Red background: Alert triggered

**Activity Types:**
- `Reset Request`: User requested password reset
- `Reset Success`: User successfully reset password

**Alert Column:**
- Shows alert badge if triggered
- Displays alert reasons below badge
- Multiple reasons separated by semicolons

## API Reference

### SuspiciousActivity Model Methods

#### log_activity(email, activity_type, ip_address, user_agent, user_id=None, country=None, city=None)
Creates a new suspicious activity record.

**Returns:** `SuspiciousActivity` object

#### detect_multiple_attempts(email, hours=1, threshold=5)
Checks for multiple password reset attempts from different IPs.

**Returns:** `(is_suspicious: bool, reason: str, count: int)`

#### detect_geographic_anomaly(email, current_ip, current_country)
Checks for password reset from unusual location.

**Returns:** `(is_suspicious: bool, reason: str)`

#### detect_time_pattern_anomaly(email, current_hour)
Checks for password reset at unusual time.

**Returns:** `(is_suspicious: bool, reason: str)`

#### check_all_patterns(email, ip_address, user_id, country=None)
Runs all detection algorithms and returns combined results.

**Returns:**
```python
{
    'is_suspicious': bool,
    'reasons': [str],
    'details': {
        'multiple_attempts': {...},
        'geographic_anomaly': {...},
        'time_pattern': {...}
    }
}
```

#### cleanup_old_records(days=90)
Deletes suspicious activity records older than specified days.

**Usage:** Run periodically via cron job or scheduled task

## Maintenance

### Cleanup Old Records

Create a scheduled task to clean up old records:

**Script: `scripts/cleanup_suspicious_activity.py`**
```python
from app import create_app
from app.models import SuspiciousActivity

app = create_app()
with app.app_context():
    retention_days = app.config.get('SUSPICIOUS_ACTIVITY_RETENTION_DAYS', 90)
    deleted = SuspiciousActivity.cleanup_old_records(days=retention_days)
    print(f"Deleted {deleted} old suspicious activity records")
```

**Cron Schedule (daily at 2 AM):**
```bash
0 2 * * * cd /path/to/app && python scripts/cleanup_suspicious_activity.py
```

### Database Maintenance

**Check Table Size:**
```sql
SELECT COUNT(*) FROM suspicious_activity;
SELECT pg_size_pretty(pg_total_relation_size('suspicious_activity'));
```

**View Recent Alerts:**
```sql
SELECT * FROM suspicious_activity 
WHERE alert_triggered = TRUE 
ORDER BY timestamp DESC 
LIMIT 10;
```

## Performance Considerations

### IP Geolocation

**Rate Limiting:**
- Free tier: 45 requests/minute
- Consider caching geolocation results by IP
- Implement exponential backoff on failures

**Timeout:**
- Current: 2 seconds
- Prevents password reset delays if API is slow
- Failed lookups don't block the reset process

### Database Queries

**Optimized Indexes:**
- Email lookups: Fast for pattern detection
- IP address lookups: Fast for geographic analysis
- Timestamp lookups: Fast for time-based queries

**Query Performance:**
- Multiple attempts detection: 1 indexed query
- Geographic anomaly: 1 indexed query (10 most recent)
- Time pattern: 1 indexed query (90-day window)

## Security Best Practices

1. **Don't Reveal Detection**
   - Don't inform users when patterns are detected
   - Continue normal password reset flow
   - Alert admins silently

2. **Monitor False Positives**
   - Review alerts regularly
   - Adjust thresholds based on your user base
   - Consider VPN usage patterns

3. **Combine with Account Lockout**
   - Suspicious activity detection complements lockout system
   - Use both for defense in depth

4. **Regular Reviews**
   - Check dashboard weekly
   - Look for emerging patterns
   - Update detection thresholds as needed

## Troubleshooting

### No Activities Showing

1. Verify database migration applied: `flask db upgrade`
2. Check configuration: `SUSPICIOUS_ACTIVITY_ENABLED=True`
3. Test password reset flow
4. Check application logs for errors

### Geolocation Not Working

1. Check internet connectivity
2. Verify API limit not exceeded (45/min)
3. Check logs for timeout errors
4. Test manually: `http://ip-api.com/json/8.8.8.8`

### Too Many False Positives

**Adjust Thresholds:**
- Increase `SUSPICIOUS_ACTIVITY_ATTEMPTS_THRESHOLD` (e.g., 7-10)
- Increase time pattern deviation (modify model method)
- Adjust geographic detection to require multiple new countries

**Consider User Behavior:**
- VPN users may trigger geographic alerts
- Mobile users may have varying IPs
- International users may have unusual time patterns

### Missing Admin Navigation Link

Update other admin templates to include the suspicious activity link:

```html
<a href="{{ url_for('auth.admin_suspicious_activity') }}" 
   class="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium">
    Suspicious Activity
</a>
```

## Related Documentation

- [Password Reset System](PASSWORD_RESET_SYSTEM.md)
- [Account Lockout System](ACCOUNT_LOCKOUT_SYSTEM.md)
- [Audit Trail System](AUDIT_TRAIL_SYSTEM.md)
- [Security Guide](SECURITY_GUIDE.md)

## Machine Learning-Based Anomaly Detection

### Overview

The ML-based anomaly detection uses an **Isolation Forest** algorithm to automatically learn normal password reset patterns and detect anomalies. This complements the rule-based detection by identifying subtle patterns that are difficult to express as explicit rules.

### Why Isolation Forest?

Isolation Forest is ideal for security anomaly detection because:
- **Isolation-based**: Anomalies are easier to isolate than normal points
- **Unsupervised**: No need to label attacks vs. normal activity
- **Efficient**: Fast training and prediction, even with large datasets
- **High-dimensional**: Works well with many features (we use 12)
- **No assumptions**: Doesn't assume normal data distribution

### Feature Engineering

The system extracts 12 features from each password reset activity:

**Temporal Features:**
1. `hour_of_day` (0-23): Hour when request occurred
2. `day_of_week` (0-6): Day of week
3. `time_since_last_activity`: Hours since last activity for this email
4. `avg_time_between_requests`: Average time between last 10 requests

**Frequency Features:**
5. `requests_last_hour`: Number of requests in last hour
6. `requests_last_day`: Number of requests in last 24 hours
7. `unique_ips_last_hour`: Different IP addresses in last hour
8. `unique_ips_last_day`: Different IP addresses in last day

**Geographic Features:**
9. `country_changes_last_day`: Number of different countries in last 24 hours
10. `is_known_country`: 1 if country seen in last 30 days, 0 if new
11. `is_known_ip`: 1 if IP seen in last 30 days, 0 if new

**User Behavior Features:**
12. `user_activity_count`: Total historical activities for this user

### Training the Model

#### Initial Training

**Prerequisites:**
- Minimum 100 suspicious activity records (1000+ recommended)
- scikit-learn and joblib installed (`pip install -r requirements.txt`)

**Command:**
```bash
python scripts/train_anomaly_detector.py
```

**With Custom Contamination:**
```bash
# 5% expected anomalies (more conservative)
python scripts/train_anomaly_detector.py --contamination 0.05

# 15% expected anomalies (more sensitive)
python scripts/train_anomaly_detector.py --contamination 0.15
```

**Skip Evaluation:**
```bash
python scripts/train_anomaly_detector.py --no-eval
```

#### Understanding Output

```
==============================================================
ML Anomaly Detection Model Training
==============================================================

Data Statistics:
  Total activities: 2543
  Alert activities: 187
  Alert rate: 7.4%

Contamination parameter: 10.0%
(Expected proportion of anomalies in training data)

Training model...
Training on 2543 samples with 12 features
✓ Model training complete: 254/2543 anomalies detected

Evaluating model performance...

Evaluation Results:
  Samples evaluated: 1000
  Anomalies detected: 98
  Known alerts: 85

Confusion Matrix:
  True Positives:  72
  False Positives: 26
  True Negatives:  889
  False Negatives: 13

Performance Metrics:
  Precision: 0.735
  Recall:    0.847
  F1 Score:  0.787

Interpretation:
  ✓ Good precision: 73.5% of detected anomalies are real alerts
  ✓ Good recall: 84.7% of real alerts are detected
  ✓ Good overall performance (F1: 0.787)
```

**Metrics Explained:**
- **Precision**: Of all ML-detected anomalies, what % are real alerts?
  - High precision = few false positives
- **Recall**: Of all real alerts, what % did ML detect?
  - High recall = few missed alerts
- **F1 Score**: Balanced measure of precision and recall
  - F1 > 0.7 is good, F1 > 0.8 is excellent

#### Periodic Retraining

**Why Retrain?**
- User behavior patterns evolve over time
- New types of legitimate activity emerge
- Attack patterns change
- Data drift can reduce accuracy

**Recommended Schedule:**
- **Weekly**: For high-traffic applications (1000+ activities/week)
- **Monthly**: For moderate-traffic applications
- **After incidents**: When new attack patterns are detected

**Automated Retraining (Cron):**
```bash
# Weekly on Sunday at 3 AM
0 3 * * 0 cd /path/to/app && python scripts/train_anomaly_detector.py >> /var/log/ml_training.log 2>&1
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task for weekly training
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\train_anomaly_detector.py" -WorkingDirectory "C:\path\to\app"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "ML_Anomaly_Training" -Description "Retrain ML anomaly detection model"
```

### Using the Model

#### Enabling ML Detection

After training, enable ML detection in `.env`:
```bash
ML_ANOMALY_DETECTION_ENABLED=True
```

#### How It Works in Production

1. **Password Reset Request**:
   - System extracts 12 features from current activity
   - ML model scores the activity (0-1 scale)
   - Threshold check: score > 0.7 or prediction = -1
   - If anomalous, adds to suspicious activity reasons

2. **Combined with Rule-Based Detection**:
   - ML detection runs alongside existing rule-based checks
   - Activity flagged if ANY detector triggers (OR logic)
   - All triggered detectors contribute to alert reasons

3. **Alert Example**:
   ```
   Suspicious Activity Detected:
   - Multiple attempts: 6 requests from different IPs in 1 hour
   - ML detected: Request from new country; 5 requests in last hour; Unusual hour: 3:00
   ```

### Model Files

**Location:** `instance/ml_models/`
- `anomaly_detector.pkl`: Trained Isolation Forest model
- `feature_scaler.pkl`: StandardScaler for feature normalization

**Size:** Typically 100KB - 1MB depending on training data size

**Backup:** Keep backups of well-performing models before retraining

### Performance Tuning

#### Adjusting Contamination

**Too Many False Positives?**
- Decrease contamination: `--contamination 0.05`
- Model becomes more conservative
- Fewer anomalies detected

**Missing Real Attacks?**
- Increase contamination: `--contamination 0.15`
- Model becomes more sensitive
- More anomalies detected

#### Feature Importance

Features most useful for detection:
1. **Frequency features** (requests per hour, unique IPs)
2. **Geographic features** (new country, new IP)
3. **Temporal features** (unusual hours, rapid succession)

### Monitoring ML Performance

#### Check Current Performance

```python
from app import create_app, db
from app.ml_anomaly_detector import ml_detector

app = create_app()
with app.app_context():
    metrics = ml_detector.evaluate_model(db.session)
    print(metrics)
```

#### Log Analysis

Watch for:
- **Precision drop**: Indicates false positives increasing
- **Recall drop**: Indicates missing real alerts
- **F1 score drop**: Overall performance degrading → Retrain model

### Troubleshooting

**Model Not Loading**
```
WARNING: ML model not found. Run training script to create model.
```
**Solution:** Train the model first:
```bash
python scripts/train_anomaly_detector.py
```

**Insufficient Training Data**
```
⚠️ Warning: Insufficient data for training (need 100+, got 47)
```
**Solution:** 
- Generate more suspicious activity data
- Wait for more password reset attempts
- Consider lowering minimum requirement in code (not recommended)

**Import Error**
```
ModuleNotFoundError: No module named 'sklearn'
```
**Solution:** Install ML dependencies:
```bash
pip install scikit-learn joblib
```

**Low Precision (Many False Positives)**
- Decrease contamination parameter
- Collect more training data
- Review false positive cases and adjust features
- Consider ensemble approach with rule-based detection

**Low Recall (Missing Attacks)**
- Increase contamination parameter
- Retrain with more diverse attack examples
- Add more discriminative features
- Lower anomaly score threshold in code

### Advanced Configuration

#### Custom Feature Selection

Edit `app/ml_anomaly_detector.py` to modify feature list:
```python
self.feature_names = [
    'hour_of_day',
    'requests_last_hour',
    # Add custom features here
]
```

#### Model Parameters

Adjust Isolation Forest parameters in `train_model()` method:
```python
self.model = IsolationForest(
    n_estimators=100,      # Number of trees (increase for better performance)
    contamination=0.1,     # Expected anomaly proportion
    max_samples='auto',    # Samples per tree
    random_state=42,       # For reproducibility
    n_jobs=-1              # Use all CPU cores
)
```

## Future Enhancements

1. **Risk Scoring**: Calculate comprehensive risk scores combining all detectors
3. **User Notifications**: Optional user alerts for suspicious activity on their account
4. **IP Reputation**: Integrate IP reputation databases
5. **Behavioral Biometrics**: Analyze typing patterns, mouse movements
6. **Threat Intelligence**: Integrate threat feeds for known malicious IPs
7. **Automated Response**: Auto-lock accounts on high-risk patterns
8. **Dashboard Analytics**: Charts and graphs for activity trends
