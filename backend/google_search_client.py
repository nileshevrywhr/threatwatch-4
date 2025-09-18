"""
Google Custom Search API Client for News Article Search
"""
import os
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GoogleCustomSearchClient:
    """
    Client for Google Custom Search API optimized for news article search
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Missing required environment variables: GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID")
        
        logger.info("Google Custom Search client initialized successfully")
    
    async def search_news_articles(
        self, 
        query: str, 
        num_results: int = 10,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Search for news articles using Google Custom Search API
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)
            days_back: Number of days to look back for articles
            
        Returns:
            Dictionary containing search results and metadata
        """
        logger.info(f"Searching for news articles: query='{query[:50]}...', num_results={num_results}, days_back={days_back}")
        
        # Create a flexible query that searches for the term in news context
        # Remove exact phrase matching and make it more flexible
        base_query = f"{query} (news OR article OR report OR breaking OR security OR threat OR incident)"
        
        # Add news source preferences but don't make them mandatory
        # This will bias towards news sites but not exclude other results
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": base_query,
            "num": min(num_results, 10),  # Google API max is 10 per request
            "dateRestrict": f"d{max(days_back, 30)}",  # Extend to 30 days if needed
            "sort": "date",  # Sort by date (newest first)
            "safe": "medium",  # Safe search
            "lr": "lang_en",  # English language results
            "gl": "us",  # Geographic location bias to US
            "tbm": "nws"  # Search news specifically
        }
        
        timeout = httpx.Timeout(30.0)  # 30 second timeout
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                logger.info("Making request to Google Custom Search API")
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                result = response.json()
                items_count = len(result.get("items", []))
                total_results = result.get("searchInformation", {}).get("totalResults", "0")
                
                logger.info(f"Search completed successfully: {items_count} items returned, {total_results} total results available")
                return result
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Google API error: {e.response.status_code}"
                logger.error(f"{error_msg} - {e.response.text}")
                
                if e.response.status_code == 429:
                    raise HTTPException(
                        status_code=429, 
                        detail="Google API rate limit exceeded. Please try again later."
                    )
                elif e.response.status_code == 403:
                    raise HTTPException(
                        status_code=403, 
                        detail="Google API key invalid or quota exceeded. Please check your API configuration."
                    )
                elif e.response.status_code == 400:
                    raise HTTPException(
                        status_code=400, 
                        detail="Invalid search parameters. Please check your query."
                    )
                else:
                    raise HTTPException(
                        status_code=e.response.status_code, 
                        detail=f"Google API error: {e.response.text[:200]}"
                    )
                    
            except httpx.TimeoutException:
                logger.error("Google API request timeout")
                raise HTTPException(
                    status_code=504, 
                    detail="Search request timeout. Please try again."
                )
                
            except Exception as e:
                logger.error(f"Unexpected error during search: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Internal search error: {str(e)}"
                )
    
    def extract_article_data(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and structure article data from Google search results
        
        Args:
            search_results: Raw Google Custom Search API response
            
        Returns:
            List of structured article data dictionaries
        """
        articles = []
        items = search_results.get("items", [])
        
        for item in items:
            try:
                # Extract basic article information
                article = {
                    "title": item.get("title", "").strip(),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "").strip(),
                    "source": self._extract_source_name(item.get("link", "")),
                    "published_date": self._extract_publish_date(item),
                    "severity": "Medium"  # Default severity for news articles
                }
                
                # Clean up snippet text
                if article["snippet"]:
                    article["snippet"] = article["snippet"].replace("...", "").strip()
                
                articles.append(article)
                
            except Exception as e:
                logger.warning(f"Error processing article item: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(articles)} articles from search results")
        return articles
    
    def _extract_source_name(self, url: str) -> str:
        """
        Extract readable source name from URL
        """
        if not url:
            return "Unknown Source"
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix
            domain = domain.replace('www.', '')
            
            # Map common news domains to readable names
            domain_mapping = {
                'reuters.com': 'Reuters',
                'bbc.com': 'BBC News',
                'cnn.com': 'CNN',
                'apnews.com': 'Associated Press',
                'npr.org': 'NPR',
                'wsj.com': 'Wall Street Journal',
                'nytimes.com': 'New York Times',
                'washingtonpost.com': 'Washington Post',
                'usatoday.com': 'USA Today',
                'foxnews.com': 'Fox News',
                'cbsnews.com': 'CBS News',
                'abcnews.go.com': 'ABC News',
                'nbcnews.com': 'NBC News'
            }
            
            if domain in domain_mapping:
                return domain_mapping[domain]
            
            # Extract main domain name for unknown sources
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[0].replace('-', ' ').title()
            
            return domain.title()
            
        except Exception:
            return "Unknown Source"
    
    def _extract_publish_date(self, item: Dict[str, Any]) -> Optional[str]:
        """
        Extract publication date from search result metadata
        """
        try:
            # Try to extract from pagemap metadata
            pagemap = item.get("pagemap", {})
            
            # Check metatags for structured date information
            metatags = pagemap.get("metatags", [])
            for tag in metatags:
                # Look for common date fields
                for date_field in ["article:published_time", "datePublished", "publishedDate", "date"]:
                    if date_field in tag and tag[date_field]:
                        try:
                            # Parse ISO format dates
                            date_str = tag[date_field]
                            if 'T' in date_str:
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                return date_obj.strftime('%Y-%m-%d')
                        except:
                            continue
            
            # Fallback: use current date minus some days (since we're searching recent articles)
            fallback_date = datetime.now() - timedelta(days=1)
            return fallback_date.strftime('%Y-%m-%d')
            
        except Exception:
            # Return recent date as fallback
            return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check to verify API connectivity and configuration
        """
        try:
            # Perform a minimal test search
            test_result = await self.search_news_articles("test", num_results=1, days_back=7)
            
            return {
                "status": "healthy",
                "api_configured": True,
                "test_search_successful": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException as e:
            return {
                "status": "unhealthy",
                "api_configured": True,
                "test_search_successful": False,
                "error": e.detail,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_configured": False,
                "test_search_successful": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }