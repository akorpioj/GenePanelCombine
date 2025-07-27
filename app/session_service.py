"""
Enhanced Session Security Service for PanelMerge Application

Provides comprehensive session management features:
- Secure session token generation and rotation
- Redis-based session storage
- Session monitoring and analytics
- Concurrent session management
- Session revocation capabilities
- Advanced security checks
"""

import logging
import secrets
import hashlib
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import request, session, current_app, g
import redis

logger = logging.getLogger(__name__)

class SessionService:
    """
    Enhanced session security service.
    
    Features:
    - Secure token generation with cryptographic randomness
    - Redis-based session storage for scalability
    - Session rotation on privilege changes
    - Concurrent session management
    - Session analytics and monitoring
    - Advanced security checks and validation
    """
    
    def __init__(self):
        self.redis_client = None
        self.session_timeout = 3600  # 1 hour default
        self.max_concurrent_sessions = 5  # Max sessions per user
        self.session_rotation_interval = 1800  # 30 minutes
        self.enable_session_analytics = True
        
    def init_app(self, app):
        """Initialize session service with Flask app"""
        self.session_timeout = app.config.get('SESSION_TIMEOUT', 3600)
        self.max_concurrent_sessions = app.config.get('MAX_CONCURRENT_SESSIONS', 5)
        self.session_rotation_interval = app.config.get('SESSION_ROTATION_INTERVAL', 1800)
        self.enable_session_analytics = app.config.get('ENABLE_SESSION_ANALYTICS', True)
        
        # Initialize Redis connection for session storage
        redis_url = app.config.get('CACHE_REDIS_URL')
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                logger.info("Redis session storage initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for session storage: {e}")
                self.redis_client = None
        
        # Configure Flask session settings
        app.config.update(
            SESSION_COOKIE_SECURE=app.config.get('REQUIRE_HTTPS', False),
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            SESSION_COOKIE_NAME='secure_session',
            PERMANENT_SESSION_LIFETIME=timedelta(seconds=self.session_timeout),
            SESSION_REFRESH_EACH_REQUEST=True
        )
        
        # Register session middleware
        app.before_request(self._before_request_handler)
        app.after_request(self._after_request_handler)
        
        logger.info("Enhanced session service initialized")
    
    def _before_request_handler(self):
        """Handle session security checks before each request"""
        if 'user_id' in session:
            # Validate session integrity
            if not self._validate_session():
                self.destroy_session()
                return
            
            # Check for session timeout
            if self._is_session_expired():
                self.destroy_session()
                logger.info("Session expired due to inactivity")
                return
            
            # Check if session needs rotation
            if self._should_rotate_session():
                self._rotate_session_id()
            
            # Update session activity
            self._update_session_activity()
    
    def _after_request_handler(self, response):
        """Handle post-request session operations"""
        # Update session analytics if enabled
        if self.enable_session_analytics and 'user_id' in session:
            self._track_session_analytics()
        
        return response
    
    def create_session(self, user_id: int, user_agent: str = None, 
                      ip_address: str = None, remember_me: bool = False) -> str:
        """
        Create a new secure session for a user.
        
        Args:
            user_id: User ID to associate with session
            user_agent: Browser user agent string
            ip_address: Client IP address
            remember_me: Whether to create a long-lived session
            
        Returns:
            session_token: Secure session token
        """
        # Generate cryptographically secure session token
        session_token = self._generate_session_token()
        
        # Check concurrent session limit
        if not self._check_concurrent_session_limit(user_id):
            # Remove oldest session if limit exceeded
            self._cleanup_oldest_session(user_id)
        
        # Create session data
        session_data = {
            'user_id': user_id,
            'session_token': session_token,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': ip_address or self._get_client_ip(),
            'user_agent': user_agent or request.headers.get('User-Agent', ''),
            'user_agent_hash': self._hash_user_agent(user_agent),
            'csrf_token': secrets.token_urlsafe(32),
            'remember_me': remember_me,
            'privilege_level': 'user',  # Track privilege escalation
            'session_rotated_at': time.time(),
            'request_count': 0,
            'security_flags': {
                'ip_changed': False,
                'ua_changed': False,
                'suspicious_activity': False
            }
        }
        
        # Calculate session timeout
        timeout = self.session_timeout
        if remember_me:
            timeout = self.session_timeout * 24  # 24x longer for remember me
        
        # Store session in Flask session
        session.permanent = remember_me
        session['user_id'] = user_id
        session['session_token'] = session_token
        session['created_at'] = session_data['created_at']
        session['last_activity'] = session_data['last_activity']
        session['csrf_token'] = session_data['csrf_token']
        session['user_agent_hash'] = session_data['user_agent_hash']
        session['ip_address'] = session_data['ip_address']
        session['privilege_level'] = session_data['privilege_level']
        session['session_rotated_at'] = session_data['session_rotated_at']
        
        # Store extended session data in Redis if available
        if self.redis_client:
            self._store_session_in_redis(session_token, session_data, timeout)
        
        # Log session creation
        self._log_session_event('session_created', user_id, {
            'session_token': session_token[:8] + '...',  # Partial token for logging
            'ip_address': session_data['ip_address'],
            'remember_me': remember_me
        })
        
        logger.info(f"Secure session created for user {user_id}")
        return session_token
    
    def destroy_session(self, session_token: str = None):
        """
        Destroy a session securely.
        
        Args:
            session_token: Specific session to destroy (optional)
        """
        current_token = session_token or session.get('session_token')
        user_id = session.get('user_id')
        
        if current_token and self.redis_client:
            # Remove from Redis storage
            self.redis_client.delete(f"session:{current_token}")
            
            # Remove from user's active sessions
            if user_id:
                self.redis_client.srem(f"user_sessions:{user_id}", current_token)
        
        # Clear Flask session
        session.clear()
        
        # Log session destruction
        if user_id:
            self._log_session_event('session_destroyed', user_id, {
                'session_token': current_token[:8] + '...' if current_token else 'unknown'
            })
        
        logger.info(f"Session destroyed for user {user_id}")
    
    def revoke_user_sessions(self, user_id: int, except_current: bool = False) -> int:
        """
        Revoke all sessions for a specific user.
        
        Args:
            user_id: User ID whose sessions to revoke
            except_current: Whether to keep the current session active
            
        Returns:
            Number of sessions revoked
        """
        if not self.redis_client:
            return 0
        
        current_token = session.get('session_token')
        user_sessions_key = f"user_sessions:{user_id}"
        
        # Get all user sessions
        session_tokens = self.redis_client.smembers(user_sessions_key)
        revoked_count = 0
        
        for token in session_tokens:
            if except_current and token == current_token:
                continue
            
            # Remove session data
            self.redis_client.delete(f"session:{token}")
            self.redis_client.srem(user_sessions_key, token)
            revoked_count += 1
        
        # Log session revocation
        self._log_session_event('sessions_revoked', user_id, {
            'revoked_count': revoked_count,
            'except_current': except_current
        })
        
        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count
    
    def get_user_sessions(self, user_id: int) -> List[Dict]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User ID to query
            
        Returns:
            List of session information dictionaries
        """
        logger.info(f"Getting sessions for user {user_id}")
        
        if not self.redis_client:
            logger.warning("Redis client not available for session retrieval")
            return []
        
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            logger.info(f"Looking for sessions in Redis key: {user_sessions_key}")
            
            session_tokens = self.redis_client.smembers(user_sessions_key)
            logger.info(f"Found {len(session_tokens)} session tokens for user {user_id}")
            
            sessions = []
            for token in session_tokens:
                try:
                    session_data = self._get_session_from_redis(token)
                    if session_data:
                        # Safely extract session info with defaults
                        created_at = session_data.get('created_at')
                        last_activity = session_data.get('last_activity')
                        
                        logger.debug(f"Session {token[:8]}... - created_at: {created_at}, last_activity: {last_activity}")
                        
                        # Skip sessions with missing critical data
                        if not created_at or not last_activity:
                            logger.warning(f"Session {token[:8]}... missing timestamp data, skipping")
                            continue
                        
                        # Return safe session info (no sensitive data)
                        sessions.append({
                            'session_id': token[:8] + '...',
                            'created_at': datetime.fromtimestamp(float(created_at)),
                            'last_activity': datetime.fromtimestamp(float(last_activity)),
                            'ip_address': session_data.get('ip_address', 'unknown'),
                            'user_agent': (session_data.get('user_agent', 'unknown')[:50] + '...') if len(session_data.get('user_agent', '')) > 50 else session_data.get('user_agent', 'unknown'),
                            'is_current': token == session.get('session_token'),
                            'remember_me': session_data.get('remember_me', False)
                        })
                        logger.debug(f"Added session {token[:8]}... to results")
                except Exception as e:
                    logger.warning(f"Error processing session {token[:8]}...: {e}")
                    continue
            
            logger.info(f"Returning {len(sessions)} valid sessions for user {user_id}")
            return sorted(sessions, key=lambda x: x['last_activity'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error retrieving user sessions for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def escalate_privileges(self, new_privilege_level: str):
        """
        Handle privilege escalation with session security.
        
        Args:
            new_privilege_level: New privilege level (e.g., 'admin', 'moderator')
        """
        if 'user_id' not in session:
            logger.warning("Cannot escalate privileges: user_id not in session")
            return False
        
        # Ensure we have a valid session token
        if 'session_token' not in session:
            logger.warning("Cannot escalate privileges: session_token not in session")
            return False
        
        old_level = session.get('privilege_level', 'user')
        
        try:
            # Rotate session on privilege escalation
            self._rotate_session_id()
            
            # Update privilege level
            session['privilege_level'] = new_privilege_level
            
            # Update in Redis if available
            if self.redis_client:
                session_token = session.get('session_token')
                if session_token:
                    session_data = self._get_session_from_redis(session_token)
                    if session_data:
                        session_data['privilege_level'] = new_privilege_level
                        self._store_session_in_redis(session_token, session_data, self.session_timeout)
            
            # Log privilege escalation
            self._log_session_event('privilege_escalated', session['user_id'], {
                'old_level': old_level,
                'new_level': new_privilege_level
            })
            
            logger.info(f"Privilege escalated for user {session['user_id']}: {old_level} -> {new_privilege_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error during privilege escalation: {e}")
            # Continue without escalation rather than failing completely
            session['privilege_level'] = new_privilege_level
            return True
    
    def _generate_session_token(self) -> str:
        """Generate a cryptographically secure session token"""
        # Generate 256 bits of randomness (32 bytes)
        random_bytes = secrets.token_bytes(32)
        
        # Add timestamp and additional entropy
        timestamp = str(time.time()).encode()
        entropy = secrets.token_bytes(16)
        
        # Create hash of combined data
        combined = random_bytes + timestamp + entropy
        token = hashlib.sha256(combined).hexdigest()
        
        return token
    
    def _validate_session(self) -> bool:
        """Validate session integrity and security"""
        session_token = session.get('session_token')
        if not session_token:
            return False
        
        # Check basic session data
        required_fields = ['user_id', 'created_at', 'last_activity']
        for field in required_fields:
            if field not in session:
                logger.warning(f"Session missing required field: {field}")
                return False
        
        # Validate session token format
        if not self._is_valid_token_format(session_token):
            logger.warning("Invalid session token format")
            return False
        
        # Check for session hijacking
        if not self._check_session_hijacking():
            logger.warning("Potential session hijacking detected")
            return False
        
        # Validate with Redis storage if available
        if self.redis_client:
            try:
                redis_data = self._get_session_from_redis(session_token)
                if not redis_data:
                    logger.warning("Session not found in Redis storage")
                    # Don't fail validation if Redis is not available or session not found
                    # Fall back to Flask session validation
                    return True
                
                # Cross-validate session data
                if redis_data['user_id'] != session['user_id']:
                    logger.warning("Session user ID mismatch")
                    return False
            except Exception as e:
                logger.warning(f"Redis validation failed, falling back to Flask session: {e}")
                # Don't fail validation due to Redis issues
                return True
        
        return True
    
    def _is_session_expired(self) -> bool:
        """Check if session has expired"""
        last_activity = session.get('last_activity')
        if not last_activity:
            return True
        
        current_time = time.time()
        return (current_time - last_activity) > self.session_timeout
    
    def _should_rotate_session(self) -> bool:
        """Check if session should be rotated"""
        last_rotation = session.get('session_rotated_at')
        if not last_rotation:
            return True
        
        current_time = time.time()
        return (current_time - last_rotation) > self.session_rotation_interval
    
    def _rotate_session_id(self):
        """Rotate session ID for security"""
        old_token = session.get('session_token')
        new_token = self._generate_session_token()
        
        # Update session
        session['session_token'] = new_token
        session['session_rotated_at'] = time.time()
        
        # Update Redis storage if available
        if self.redis_client and old_token:
            # Get existing session data
            session_data = self._get_session_from_redis(old_token)
            if session_data:
                # Ensure we have user_id in session_data, fallback to Flask session
                user_id = session_data.get('user_id') or session.get('user_id')
                
                if user_id:
                    # Remove old session
                    self.redis_client.delete(f"session:{old_token}")
                    self.redis_client.srem(f"user_sessions:{user_id}", old_token)
                    
                    # Store with new token
                    session_data['session_token'] = new_token
                    session_data['session_rotated_at'] = time.time()
                    # Ensure user_id is in session_data
                    session_data['user_id'] = user_id
                    self._store_session_in_redis(new_token, session_data, self.session_timeout)
                else:
                    logger.warning("Could not find user_id for session rotation, creating minimal session data")
                    # Create minimal session data if user_id is missing
                    session_data = {
                        'user_id': session.get('user_id'),
                        'session_token': new_token,
                        'session_rotated_at': time.time(),
                        'created_at': time.time(),
                        'last_activity': time.time()
                    }
                    if session_data['user_id']:
                        self._store_session_in_redis(new_token, session_data, self.session_timeout)
        
        logger.info("Session ID rotated for security")
    
    def _check_session_hijacking(self) -> bool:
        """Check for potential session hijacking"""
        # Check User-Agent consistency
        current_ua = request.headers.get('User-Agent', '')
        stored_ua_hash = session.get('user_agent_hash')
        current_ua_hash = self._hash_user_agent(current_ua)
        
        if stored_ua_hash and stored_ua_hash != current_ua_hash:
            return False
        
        # Check IP address consistency (with some flexibility for legitimate changes)
        current_ip = self._get_client_ip()
        stored_ip = session.get('ip_address')
        
        if stored_ip and stored_ip != current_ip:
            # Log IP change but don't immediately invalidate
            # (user might have legitimate IP changes)
            self._log_session_event('ip_address_changed', session.get('user_id'), {
                'old_ip': stored_ip,
                'new_ip': current_ip
            })
            session['ip_address'] = current_ip
        
        return True
    
    def _update_session_activity(self):
        """Update session activity timestamp"""
        current_time = time.time()
        session['last_activity'] = current_time
        
        # Update in Redis if available
        if self.redis_client:
            session_token = session.get('session_token')
            if session_token:
                self.redis_client.hset(f"session:{session_token}", 'last_activity', current_time)
    
    def _check_concurrent_session_limit(self, user_id: int) -> bool:
        """Check if user has exceeded concurrent session limit"""
        if not self.redis_client:
            return True
        
        user_sessions = self.redis_client.scard(f"user_sessions:{user_id}")
        return user_sessions < self.max_concurrent_sessions
    
    def _cleanup_oldest_session(self, user_id: int):
        """Remove the oldest session for a user"""
        if not self.redis_client:
            return
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_tokens = self.redis_client.smembers(user_sessions_key)
        
        if not session_tokens:
            return
        
        # Find oldest session
        oldest_token = None
        oldest_time = float('inf')
        
        for token in session_tokens:
            session_data = self._get_session_from_redis(token)
            if session_data and session_data['created_at'] < oldest_time:
                oldest_time = session_data['created_at']
                oldest_token = token
        
        if oldest_token:
            self.redis_client.delete(f"session:{oldest_token}")
            self.redis_client.srem(user_sessions_key, oldest_token)
            logger.info(f"Removed oldest session for user {user_id}")
    
    def _store_session_in_redis(self, session_token: str, session_data: Dict, timeout: int):
        """Store session data in Redis"""
        if not self.redis_client:
            return
        
        try:
            # Convert session data for Redis storage (Redis requires string values)
            redis_data = {}
            for key, value in session_data.items():
                if isinstance(value, bool):
                    redis_data[key] = str(value).lower()
                elif isinstance(value, dict):
                    redis_data[key] = json.dumps(value)
                elif key == 'request_count':
                    # Ensure request_count is stored as integer string for HINCRBY
                    redis_data[key] = str(int(value) if value is not None else 0)
                elif value is None:
                    redis_data[key] = ''
                else:
                    redis_data[key] = str(value)
            
            # Store session data
            self.redis_client.hset(f"session:{session_token}", mapping=redis_data)
            self.redis_client.expire(f"session:{session_token}", timeout)
            
            # Add to user's session set
            user_id = session_data['user_id']
            self.redis_client.sadd(f"user_sessions:{user_id}", session_token)
            self.redis_client.expire(f"user_sessions:{user_id}", timeout)
            
        except Exception as e:
            logger.error(f"Failed to store session in Redis: {e}")
    
    def _get_session_from_redis(self, session_token: str) -> Optional[Dict]:
        """Retrieve session data from Redis"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.hgetall(f"session:{session_token}")
            if data:
                # Convert data back to appropriate types
                for field in ['user_id', 'created_at', 'last_activity', 'session_rotated_at', 'request_count']:
                    if field in data and data[field]:
                        if field == 'user_id':
                            data[field] = int(data[field])
                        else:
                            data[field] = float(data[field])
                
                # Convert boolean fields
                for field in ['remember_me']:
                    if field in data and data[field]:
                        data[field] = data[field].lower() == 'true'
                
                # Convert JSON fields
                for field in ['security_flags']:
                    if field in data and data[field]:
                        try:
                            data[field] = json.loads(data[field])
                        except json.JSONDecodeError:
                            data[field] = {}
                
                return data
        except Exception as e:
            logger.error(f"Failed to retrieve session from Redis: {e}")
        
        return None
    
    def _track_session_analytics(self):
        """Track session analytics and patterns"""
        if not self.redis_client:
            return
        
        user_id = session.get('user_id')
        if not user_id:
            return
        
        # Update request counter
        session_token = session.get('session_token')
        if session_token:
            try:
                # Try to increment the request count
                self.redis_client.hincrby(f"session:{session_token}", 'request_count', 1)
            except redis.ResponseError as e:
                if "hash value is not an integer" in str(e):
                    # Reset the request count to 1 if it's not an integer
                    self.redis_client.hset(f"session:{session_token}", 'request_count', '1')
                else:
                    # Log other Redis errors but don't fail
                    logger.warning(f"Redis analytics error: {e}")
            except Exception as e:
                logger.warning(f"Session analytics error: {e}")
        
        # Track daily active sessions
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            self.redis_client.sadd(f"daily_active_sessions:{today}", session_token)
            self.redis_client.expire(f"daily_active_sessions:{today}", 86400 * 7)  # Keep for 7 days
        except Exception as e:
            logger.warning(f"Daily session tracking error: {e}")
    
    def _hash_user_agent(self, user_agent: str) -> str:
        """Create a hash of the user agent for comparison"""
        if not user_agent:
            return ''
        return hashlib.sha256(user_agent.encode()).hexdigest()[:16]
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address"""
        # Check for proxy headers
        for header in ['X-Forwarded-For', 'X-Real-IP', 'X-Forwarded-Host']:
            if header in request.headers:
                ip = request.headers[header].split(',')[0].strip()
                if ip:
                    return ip
        return request.remote_addr or 'unknown'
    
    def _is_valid_token_format(self, token: str) -> bool:
        """Validate session token format"""
        if not token or len(token) != 64:  # SHA256 hex = 64 chars
            return False
        
        # Check if it's valid hex
        try:
            int(token, 16)
            return True
        except ValueError:
            return False
    
    def _log_session_event(self, event_type: str, user_id: int, details: Dict = None):
        """Log session-related events"""
        try:
            # Use the correct AuditService method signature
            from .audit_service import AuditService
            
            # Create action description based on event type
            action_descriptions = {
                'session_created': 'User session created',
                'session_destroyed': 'User session destroyed',
                'sessions_revoked': 'User sessions revoked',
                'privilege_escalated': 'User privileges escalated',
                'ip_address_changed': 'Session IP address changed'
            }
            
            action_description = action_descriptions.get(event_type, f'Session event: {event_type}')
            
            AuditService.log_action(
                action_type='SESSION_MANAGEMENT',
                user_id=user_id,
                action_description=action_description,
                details=details or {}
            )
        except Exception as e:
            logger.error(f"Failed to log session event: {e}")


# Global session service instance
session_service = SessionService()


def init_session_service(app):
    """Initialize enhanced session service with Flask app"""
    session_service.init_app(app)
    return session_service
