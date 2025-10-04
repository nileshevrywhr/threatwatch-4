"""
Monitor Engine - Threat Scanning Logic
======================================

This is the core scanning engine that:
1. Takes a monitoring term
2. Searches Google for relevant news
3. Analyzes results with AI
4. Decides if an alert should be generated
5. Creates alerts for detected threats

Flow:
----
Monitor → Search Google → Get Articles → AI Analysis → Generate Alert

Example:
-------
Monitor: "ransomware attacks on healthcare"
→ Search Google for recent news
→ Find 10 relevant articles
→ Send to LLM for analysis
→ LLM determines: High severity, 3 key threats identified
→ Create alert with threat summary
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import logging
import asyncio

from mongodb_models import (
    MonitorModel,
    AlertModel,
    SeverityLevel,
    AlertHistoryModel,
    APICosts,
    ScanMetadata
)
from google_search_client import GoogleCustomSearchClient
from cost_tracker import CostTracker

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    from llm_fallback import LlmChat, UserMessage
    EMERGENT_AVAILABLE = False

logger = logging.getLogger(__name__)


class MonitorEngine:
    """
    Core engine for scanning monitors and detecting threats
    """
    
    def __init__(self):
        """Initialize monitoring engine with required services"""
        self.google_client = GoogleCustomSearchClient()
        self.cost_tracker = CostTracker()
    
    async def scan_monitor(
        self,
        monitor: MonitorModel
    ) -> Tuple[Optional[AlertModel], AlertHistoryModel]:
        """
        Scan a monitor for new threats
        
        This is the main scanning function called by Celery tasks
        
        Steps:
        1. Build search query from monitor keywords
        2. Search Google for recent articles
        3. Filter and rank results
        4. Analyze with LLM
        5. Determine if alert is needed
        6. Create alert if threshold met
        7. Record scan history
        
        Args:
            monitor: MonitorModel to scan
        
        Returns:
            Tuple of (AlertModel or None, AlertHistoryModel)
            - AlertModel: Created alert if threat detected, None otherwise
            - AlertHistoryModel: Record of the scan
        """
        scan_start = datetime.now(timezone.utc)
        logger.info(f"🔍 Scanning monitor: {monitor.term} (ID: {monitor.id})")
        
        # Initialize history record
        history = AlertHistoryModel(
            monitor_id=monitor.id,
            scan_timestamp=scan_start
        )
        
        try:
            # Step 1: Build search query
            search_query = self._build_search_query(monitor)
            history.scan_metadata.query_variations = [search_query]
            
            # Step 2: Search Google
            logger.info(f"  📡 Searching Google: '{search_query}'")
            search_results = self.google_client.search_news(
                query=search_query,
                days=1,  # Last 24 hours for monitoring
                num_results=10
            )
            
            if not search_results.get('success'):
                error_msg = search_results.get('error', 'Unknown error')
                logger.error(f"  ❌ Google search failed: {error_msg}")
                history.success = False
                history.errors.append(f"Google search failed: {error_msg}")
                history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
                return None, history
            
            articles = search_results.get('articles', [])
            history.articles_processed = len(articles)
            
            # Track Google API costs
            history.api_costs.google_search_queries = 1
            
            logger.info(f"  📊 Found {len(articles)} articles")
            
            if len(articles) == 0:
                logger.info(f"  ℹ️  No new articles found")
                history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
                return None, history
            
            # Step 3: Filter relevant articles
            relevant_articles = self._filter_articles(articles, monitor)
            logger.info(f"  ✅ {len(relevant_articles)} relevant articles after filtering")
            
            if len(relevant_articles) == 0:
                logger.info(f"  ℹ️  No relevant articles after filtering")
                history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
                return None, history
            
            # Step 4: Analyze with LLM
            logger.info(f"  🤖 Analyzing articles with AI...")
            analysis_result = await self._analyze_with_llm(
                monitor=monitor,
                articles=relevant_articles
            )
            
            if not analysis_result.get('success'):
                error_msg = analysis_result.get('error', 'LLM analysis failed')
                logger.error(f"  ❌ AI analysis failed: {error_msg}")
                history.success = False
                history.errors.append(f"AI analysis failed: {error_msg}")
                history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
                return None, history
            
            # Track LLM costs
            llm_usage = analysis_result.get('usage', {})
            history.api_costs.llm_input_tokens = llm_usage.get('input_tokens', 0)
            history.api_costs.llm_output_tokens = llm_usage.get('output_tokens', 0)
            history.api_costs.llm_tokens = llm_usage.get('total_tokens', 0)
            
            # Step 5: Check if alert is needed
            threat_assessment = analysis_result.get('assessment', {})
            severity = self._parse_severity(threat_assessment.get('severity', 'low'))
            
            logger.info(f"  📈 Threat severity: {severity.value}")
            
            # Only create alert if severity meets monitor's threshold
            if not self._meets_threshold(severity, monitor.severity_threshold):
                logger.info(f"  ⚠️  Severity {severity.value} below threshold {monitor.severity_threshold.value}")
                history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
                return None, history
            
            # Step 6: Create alert
            logger.info(f"  🚨 Creating alert (severity: {severity.value})...")
            alert = await self._create_alert_from_analysis(
                monitor=monitor,
                articles=relevant_articles,
                analysis=threat_assessment,
                severity=severity
            )
            
            if alert:
                history.alerts_generated = 1
                logger.info(f"  ✅ Alert created: {alert.id}")
            
            # Calculate total costs
            google_cost = history.api_costs.google_search_queries * 0.005  # $5 per 1000 queries
            llm_cost = self.cost_tracker._calculate_cost(
                history.api_costs.llm_input_tokens,
                history.api_costs.llm_output_tokens,
                "gpt-4o"
            )
            history.api_costs.total_cost = google_cost + llm_cost
            
            # Finalize history
            history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
            history.success = True
            
            logger.info(f"✅ Scan complete in {history.scan_duration:.1f}s (Cost: ${history.api_costs.total_cost:.4f})")
            
            return alert, history
            
        except Exception as e:
            logger.error(f"❌ Scan failed: {str(e)}")
            history.success = False
            history.errors.append(str(e))
            history.scan_duration = (datetime.now(timezone.utc) - scan_start).total_seconds()
            return None, history
    
    def _build_search_query(self, monitor: MonitorModel) -> str:
        """
        Build optimized Google search query from monitor
        
        Combines main term with keywords and exclusions
        
        Args:
            monitor: Monitor to build query for
        
        Returns:
            Search query string
        """
        # Start with main term
        query = monitor.term
        
        # Add additional keywords (OR logic)
        if monitor.keywords:
            additional_terms = " OR ".join(monitor.keywords[:3])  # Limit to 3 for performance
            query = f"{query} ({additional_terms})"
        
        # Add exclusions (NOT logic)
        if monitor.exclude_keywords:
            exclusions = " ".join([f"-{keyword}" for keyword in monitor.exclude_keywords[:3]])
            query = f"{query} {exclusions}"
        
        return query
    
    def _filter_articles(
        self,
        articles: List[Dict],
        monitor: MonitorModel
    ) -> List[Dict]:
        """
        Filter articles based on relevance
        
        Filters out:
        - Articles containing excluded keywords
        - Duplicate URLs
        - Articles with very short snippets
        
        Args:
            articles: Raw articles from Google
            monitor: Monitor with filter criteria
        
        Returns:
            Filtered list of articles
        """
        filtered = []
        seen_urls = set()
        
        for article in articles:
            url = article.get('url', '')
            snippet = article.get('snippet', '')
            title = article.get('title', '')
            
            # Skip duplicates
            if url in seen_urls:
                continue
            
            # Skip if too short
            if len(snippet) < 50:
                continue
            
            # Check for excluded keywords
            exclude = False
            for keyword in monitor.exclude_keywords:
                if keyword.lower() in title.lower() or keyword.lower() in snippet.lower():
                    exclude = True
                    break
            
            if not exclude:
                filtered.append(article)
                seen_urls.add(url)
        
        return filtered
    
    async def _analyze_with_llm(
        self,
        monitor: MonitorModel,
        articles: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze articles with LLM to assess threats
        
        Sends articles to GPT-4o for threat analysis
        
        Args:
            monitor: Monitor being scanned
            articles: Relevant articles to analyze
        
        Returns:
            Dictionary with analysis results
        """
        try:
            # Build prompt for LLM
            prompt = self._build_analysis_prompt(monitor, articles)
            
            # Initialize LLM
            llm = LlmChat(model="gpt-4o")
            
            # Get analysis
            response = llm.send_message_to_llm(
                user_message=UserMessage(content=prompt),
                system_prompt="""You are a cybersecurity threat analyst. Analyze the provided news articles and assess the threat level.

Respond in the following JSON format:
{
  "severity": "low|medium|high|critical",
  "confidence": 0.85,
  "title": "Brief threat title",
  "summary": "2-3 sentence summary of the threat",
  "key_threats": ["Threat 1", "Threat 2", "Threat 3"],
  "attack_vectors": ["phishing", "malware"],
  "affected_sectors": ["healthcare", "finance"],
  "geographical_scope": ["US", "Europe"],
  "recommendations": "Brief actionable recommendations"
}"""
            )
            
            # Parse response
            analysis_text = response.get('content', '')
            
            # Extract JSON from response
            import json
            import re
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: parse as plain text
                analysis = {
                    "severity": "medium",
                    "confidence": 0.5,
                    "title": f"Threats detected for {monitor.term}",
                    "summary": analysis_text[:300],
                    "key_threats": [],
                    "attack_vectors": [],
                    "affected_sectors": [],
                    "geographical_scope": [],
                    "recommendations": "Review sources for details"
                }
            
            return {
                "success": True,
                "assessment": analysis,
                "usage": response.get('usage', {})
            }
            
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_analysis_prompt(
        self,
        monitor: MonitorModel,
        articles: List[Dict]
    ) -> str:
        """
        Build prompt for LLM analysis
        
        Args:
            monitor: Monitor being scanned
            articles: Articles to include in prompt
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following cybersecurity news articles related to "{monitor.term}".

Assess the threat level and provide a comprehensive analysis.

ARTICLES:
"""
        
        for i, article in enumerate(articles[:5], 1):  # Limit to 5 articles
            prompt += f"\n{i}. {article.get('title', 'Untitled')}\n"
            prompt += f"   Source: {article.get('domain', 'Unknown')}\n"
            prompt += f"   Date: {article.get('date', 'Unknown')}\n"
            prompt += f"   {article.get('snippet', '')}\n"
        
        return prompt
    
    async def _create_alert_from_analysis(
        self,
        monitor: MonitorModel,
        articles: List[Dict],
        analysis: Dict,
        severity: SeverityLevel
    ) -> Optional[AlertModel]:
        """
        Create AlertModel from analysis results
        
        Args:
            monitor: Source monitor
            articles: Source articles
            analysis: LLM analysis results
            severity: Determined severity
        
        Returns:
            AlertModel or None
        """
        try:
            # Convert articles to AlertSource format
            sources = []
            for article in articles[:10]:  # Limit to 10 sources
                sources.append({
                    "title": article.get('title', 'Untitled'),
                    "url": article.get('url', ''),
                    "domain": article.get('domain', 'Unknown'),
                    "published": datetime.fromisoformat(article['date'].replace('Z', '+00:00')) if article.get('date') else None,
                    "snippet": article.get('snippet', ''),
                    "relevance_score": 0.8  # Could implement better scoring
                })
            
            # Create threat indicators
            threat_indicators = {
                "attack_vectors": analysis.get('attack_vectors', []),
                "affected_sectors": analysis.get('affected_sectors', []),
                "geographical_scope": analysis.get('geographical_scope', []),
                "threat_actors": []
            }
            
            # Create alert
            alert = AlertModel(
                monitor_id=monitor.id,
                user_id=monitor.user_id,
                title=analysis.get('title', f"Threat detected: {monitor.term}"),
                summary=analysis.get('summary', 'New threat detected'),
                severity=severity,
                confidence_score=analysis.get('confidence', 0.5),
                source_count=len(sources),
                sources=sources,
                threat_indicators=threat_indicators
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            return None
    
    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """
        Parse severity string to SeverityLevel enum
        
        Args:
            severity_str: Severity as string
        
        Returns:
            SeverityLevel enum
        """
        severity_map = {
            'low': SeverityLevel.LOW,
            'medium': SeverityLevel.MEDIUM,
            'high': SeverityLevel.HIGH,
            'critical': SeverityLevel.CRITICAL
        }
        
        return severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)
    
    def _meets_threshold(
        self,
        severity: SeverityLevel,
        threshold: SeverityLevel
    ) -> bool:
        """
        Check if severity meets or exceeds threshold
        
        Severity ranking: LOW < MEDIUM < HIGH < CRITICAL
        
        Args:
            severity: Detected severity
            threshold: Minimum severity required
        
        Returns:
            True if severity >= threshold
        """
        severity_rank = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4
        }
        
        return severity_rank.get(severity, 0) >= severity_rank.get(threshold, 0)
