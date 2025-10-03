"""
PostHog Analytics Service for ThreatWatch
Comprehensive analytics tracking for user journey, business metrics, and technical events
"""
import os
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from posthog import Posthog
from enum import Enum

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Event priority levels for different tracking scenarios"""
    CRITICAL = "critical"  # Revenue, security events
    HIGH = "high"         # User lifecycle events
    MEDIUM = "medium"     # Feature usage, engagement
    LOW = "low"          # Page views, clicks

class ThreatWatchAnalytics:
    """
    Centralized analytics service for ThreatWatch application
    Tracks user journey, business metrics, and technical events
    """
    
    def __init__(self):
        self.posthog = None
        self.is_enabled = False
        self._initialize_posthog()
        
    def _initialize_posthog(self):
        """Initialize PostHog client with configuration"""
        try:
            api_key = os.getenv('POSTHOG_API_KEY')
            host = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
            
            if not api_key:
                logger.warning("PostHog API key not configured. Analytics disabled.")
                return
                
            self.posthog = Posthog(
                project_api_key=api_key,
                host=host,
                debug=os.getenv('POSTHOG_DEBUG', 'False').lower() == 'true',
                sync_mode=os.getenv('POSTHOG_SYNC_MODE', 'False').lower() == 'true',
                enable_exception_autocapture=True,
                disable_geoip=False,
                timeout=30
            )
            
            self.is_enabled = True
            logger.info("PostHog analytics initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostHog: {e}")
            self.is_enabled = False
    
    def _track_event(
        self, 
        distinct_id: str, 
        event: str, 
        properties: Dict[str, Any],
        priority: EventPriority = EventPriority.MEDIUM
    ) -> bool:
        """
        Internal method to track events with error handling and standardization
        """
        if not self.is_enabled or not self.posthog:
            return False
            
        try:
            # Add standard properties to all events
            standard_properties = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'application': 'threatwatch',
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'priority': priority.value,
                'tracking_source': 'backend'
            }
            
            # Merge properties
            final_properties = {**standard_properties, **properties}
            
            # Track the event
            self.posthog.capture(
                distinct_id=distinct_id,
                event=event,
                properties=final_properties
            )
            
            # Flush immediately for critical events
            if priority == EventPriority.CRITICAL:
                self.posthog.flush()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event '{event}': {e}")
            return False
    
    def identify_user(self, user_id: str, user_properties: Dict[str, Any]):
        """
        Identify user and set user properties for analytics
        """
        if not self.is_enabled:
            return
            
        try:
            # Set user identification
            self.posthog.identify(user_id, user_properties)
            
            # Also set as person properties
            self.posthog.set_person_properties(user_id, user_properties)
            
            logger.debug(f"User identified: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to identify user {user_id}: {e}")
    
    # ============ USER JOURNEY EVENTS ============
    
    def track_user_signup(
        self, 
        user_id: str, 
        email: str, 
        plan_type: str = 'free',
        signup_method: str = 'email',
        referrer: Optional[str] = None,
        utm_data: Optional[Dict[str, str]] = None
    ):
        """Track user registration - Key Metric #1: Signups"""
        properties = {
            'user_id': user_id,
            'email': email,
            'plan_type': plan_type,
            'signup_method': signup_method,
            'referrer': referrer,
            'is_paid_signup': plan_type != 'free'
        }
        
        # Add UTM tracking data
        if utm_data:
            for key, value in utm_data.items():
                if key.startswith('utm_'):
                    properties[key] = value
        
        self._track_event(
            distinct_id=user_id,
            event='user_signup',
            properties=properties,
            priority=EventPriority.CRITICAL
        )
        
        # Set user properties for identification
        user_props = {
            'email': email,
            'plan_type': plan_type,
            'signup_date': datetime.now(timezone.utc).isoformat(),
            'signup_method': signup_method
        }
        
        self.identify_user(user_id, user_props)
    
    def track_user_login(
        self, 
        user_id: str, 
        email: str,
        login_method: str = 'password',
        session_id: Optional[str] = None
    ):
        """Track user login events"""
        properties = {
            'user_id': user_id,
            'email': email,
            'login_method': login_method,
            'session_id': session_id
        }
        
        self._track_event(
            distinct_id=user_id,
            event='user_login',
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    def track_subscription_change(
        self, 
        user_id: str, 
        from_plan: str, 
        to_plan: str, 
        revenue: float = 0.0,
        payment_method: str = 'stripe'
    ):
        """Track subscription upgrades/downgrades - Key Metric #5: Revenue Tracking"""
        properties = {
            'user_id': user_id,
            'from_plan': from_plan,
            'to_plan': to_plan,
            'revenue': revenue,
            'currency': 'USD',
            'payment_method': payment_method,
            'is_upgrade': to_plan != 'free' and from_plan == 'free',
            'is_downgrade': to_plan == 'free' and from_plan != 'free'
        }
        
        self._track_event(
            distinct_id=user_id,
            event='subscription_change',
            properties=properties,
            priority=EventPriority.CRITICAL
        )
    
    # ============ BUSINESS METRICS EVENTS ============
    
    def track_quick_scan_initiated(
        self, 
        user_id: str, 
        query: str,
        user_plan: str,
        scans_remaining: int = 0
    ):
        """Track when user starts a Quick Scan - Key Metric #2: Searches per user"""
        properties = {
            'user_id': user_id,
            'query': query,
            'user_plan': user_plan,
            'scans_remaining': scans_remaining,
            'query_length': len(query),
            'query_category': self._categorize_query(query)
        }
        
        self._track_event(
            distinct_id=user_id,
            event='quick_scan_initiated',
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    def track_quick_scan_completed(
        self, 
        user_id: str, 
        query: str,
        scan_duration: float,
        articles_found: int,
        llm_tokens_used: int,
        total_cost: float,
        success: bool = True
    ):
        """Track completed Quick Scan with performance metrics"""
        properties = {
            'user_id': user_id,
            'query': query,
            'scan_duration_seconds': scan_duration,
            'articles_found': articles_found,
            'llm_tokens_used': llm_tokens_used,
            'total_cost': total_cost,
            'success': success,
            'performance_tier': self._classify_performance(scan_duration),
            'cost_efficiency': llm_tokens_used / max(articles_found, 1)
        }
        
        self._track_event(
            distinct_id=user_id,
            event='quick_scan_completed',
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    def track_pdf_report_generated(
        self, 
        user_id: str, 
        query: str,
        report_size_kb: float,
        generation_time: float
    ):
        """Track PDF report generation"""
        properties = {
            'user_id': user_id,
            'query': query,
            'report_size_kb': report_size_kb,
            'generation_time_seconds': generation_time,
            'file_format': 'pdf'
        }
        
        self._track_event(
            distinct_id=user_id,
            event='pdf_report_generated',
            properties=properties,
            priority=EventPriority.MEDIUM
        )
    
    def track_pdf_report_downloaded(
        self, 
        user_id: str, 
        query: str,
        report_id: str,
        download_method: str = 'browser'
    ):
        """Track PDF report downloads - Key Metric #3: Report downloads"""
        properties = {
            'user_id': user_id,
            'query': query,
            'report_id': report_id,
            'download_method': download_method,
            'download_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._track_event(
            distinct_id=user_id,
            event='pdf_report_downloaded',
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    # ============ DROP-OFF ANALYSIS EVENTS - Key Metric #4 ============
    
    def track_funnel_step(
        self, 
        user_id: str, 
        funnel_name: str, 
        step: str, 
        completed: bool = True,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Track funnel progression for drop-off analysis"""
        properties = {
            'user_id': user_id,
            'funnel_name': funnel_name,
            'step': step,
            'completed': completed,
            'step_number': self._get_step_number(funnel_name, step)
        }
        
        if additional_data:
            properties.update(additional_data)
        
        event_name = f'funnel_{funnel_name}_{step}'
        if not completed:
            event_name += '_abandoned'
        
        self._track_event(
            distinct_id=user_id,
            event=event_name,
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    def track_user_drop_off(
        self, 
        user_id: str, 
        current_step: str, 
        expected_step: str,
        time_on_step: float,
        context: Dict[str, Any]
    ):
        """Track when users drop off without completing expected actions"""
        properties = {
            'user_id': user_id,
            'current_step': current_step,
            'expected_step': expected_step,
            'time_on_step_seconds': time_on_step,
            'drop_off_point': current_step,
            **context
        }
        
        self._track_event(
            distinct_id=user_id,
            event='user_drop_off',
            properties=properties,
            priority=EventPriority.HIGH
        )
    
    # ============ TECHNICAL ERROR EVENTS ============
    
    def track_error(
        self, 
        user_id: Optional[str], 
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        severity: str = 'error'
    ):
        """Track technical errors and exceptions"""
        properties = {
            'error_type': error_type,
            'error_message': error_message[:500],  # Truncate long messages
            'severity': severity,
            'context': context,
            'stack_trace': context.get('stack_trace', ''),
            'request_path': context.get('request_path', ''),
            'user_agent': context.get('user_agent', '')
        }
        
        if user_id:
            properties['user_id'] = user_id
        
        self._track_event(
            distinct_id=user_id or 'anonymous',
            event='error_occurred',
            properties=properties,
            priority=EventPriority.CRITICAL
        )
    
    def track_api_performance(
        self, 
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None
    ):
        """Track API performance metrics"""
        properties = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time_ms': response_time * 1000,
            'status_category': self._categorize_status_code(status_code),
            'performance_tier': self._classify_performance(response_time)
        }
        
        if user_id:
            properties['user_id'] = user_id
        
        self._track_event(
            distinct_id=user_id or 'system',
            event='api_performance',
            properties=properties,
            priority=EventPriority.LOW
        )
    
    # ============ UTILITY METHODS ============
    
    def _categorize_query(self, query: str) -> str:
        """Categorize search queries for analysis"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ['ransomware', 'malware', 'virus']):
            return 'malware_threats'
        elif any(term in query_lower for term in ['data breach', 'leak', 'hack']):
            return 'data_security'
        elif any(term in query_lower for term in ['phishing', 'social engineering']):
            return 'social_attacks'
        elif any(term in query_lower for term in ['vulnerability', 'exploit', 'cve']):
            return 'vulnerabilities'
        else:
            return 'general_security'
    
    def _classify_performance(self, duration: float) -> str:
        """Classify performance based on duration"""
        if duration < 1.0:
            return 'excellent'
        elif duration < 3.0:
            return 'good'
        elif duration < 5.0:
            return 'acceptable'
        else:
            return 'slow'
    
    def _categorize_status_code(self, status_code: int) -> str:
        """Categorize HTTP status codes"""
        if 200 <= status_code < 300:
            return 'success'
        elif 300 <= status_code < 400:
            return 'redirect'
        elif 400 <= status_code < 500:
            return 'client_error'
        else:
            return 'server_error'
    
    def _get_step_number(self, funnel_name: str, step: str) -> int:
        """Get step number for funnel analysis"""
        funnel_steps = {
            'user_onboarding': {
                'signup': 1,
                'email_verification': 2,
                'profile_setup': 3,
                'first_scan': 4
            },
            'scan_to_download': {
                'scan_initiated': 1,
                'scan_completed': 2,
                'pdf_generated': 3,
                'pdf_downloaded': 4
            },
            'conversion': {
                'signup': 1,
                'first_scan': 2,
                'limit_reached': 3,
                'upgrade_viewed': 4,
                'payment_completed': 5
            }
        }
        
        return funnel_steps.get(funnel_name, {}).get(step, 0)
    
    def flush_events(self):
        """Manually flush events to PostHog"""
        if self.is_enabled and self.posthog:
            try:
                self.posthog.flush()
            except Exception as e:
                logger.error(f"Failed to flush PostHog events: {e}")
    
    def shutdown(self):
        """Gracefully shutdown analytics service"""
        if self.is_enabled and self.posthog:
            try:
                self.posthog.flush()
                self.posthog.shutdown()
                logger.info("PostHog analytics shutdown completed")
            except Exception as e:
                logger.error(f"Error during PostHog shutdown: {e}")

# Global analytics instance
analytics = ThreatWatchAnalytics()