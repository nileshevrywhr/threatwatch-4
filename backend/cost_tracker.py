"""
Cost Tracking Module for ThreatWatch
Tracks and calculates costs for LLM usage and Google Custom Search API calls
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

@dataclass
class LLMUsage:
    """Track LLM token usage and costs"""
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: Decimal
    output_cost: Decimal
    total_cost: Decimal
    request_timestamp: datetime

@dataclass
class GoogleAPIUsage:
    """Track Google Custom Search API usage and costs"""
    queries_made: int
    total_results_returned: int
    api_calls_count: int
    cost_per_query: Decimal
    total_cost: Decimal
    request_timestamp: datetime

class CostTracker:
    """
    Central cost tracking and calculation system
    """
    
    # Current pricing as of 2025 (in USD)
    # GPT-4o pricing (per 1M tokens)
    GPT_4O_INPUT_COST_PER_1M = Decimal('2.50')  # $2.50 per 1M input tokens
    GPT_4O_OUTPUT_COST_PER_1M = Decimal('10.00')  # $10.00 per 1M output tokens
    
    # Google Custom Search API pricing
    GOOGLE_SEARCH_COST_PER_1000_QUERIES = Decimal('5.00')  # $5.00 per 1000 queries
    GOOGLE_SEARCH_FREE_QUERIES_PER_DAY = 100  # First 100 queries per day are free
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_llm_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        response_metadata: Optional[Dict] = None
    ) -> LLMUsage:
        """
        Calculate LLM usage costs based on token consumption
        
        Args:
            model: Model name (e.g., 'gpt-4o')
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            response_metadata: Additional metadata from LLM response
            
        Returns:
            LLMUsage object with detailed cost breakdown
        """
        try:
            # Normalize model name
            model_lower = model.lower()
            
            # Calculate costs based on model type
            if 'gpt-4o' in model_lower:
                input_cost = (Decimal(input_tokens) / Decimal('1000000')) * self.GPT_4O_INPUT_COST_PER_1M
                output_cost = (Decimal(output_tokens) / Decimal('1000000')) * self.GPT_4O_OUTPUT_COST_PER_1M
            else:
                # Default to GPT-4o pricing for unknown models
                self.logger.warning(f"Unknown model '{model}', using GPT-4o pricing")
                input_cost = (Decimal(input_tokens) / Decimal('1000000')) * self.GPT_4O_INPUT_COST_PER_1M
                output_cost = (Decimal(output_tokens) / Decimal('1000000')) * self.GPT_4O_OUTPUT_COST_PER_1M
            
            total_tokens = input_tokens + output_tokens
            total_cost = input_cost + output_cost
            
            # Round to 6 decimal places for precision
            input_cost = input_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            output_cost = output_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            total_cost = total_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            usage = LLMUsage(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                request_timestamp=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"LLM cost calculated: {model} - {total_tokens} tokens = ${total_cost}")
            return usage
            
        except Exception as e:
            self.logger.error(f"Error calculating LLM cost: {e}")
            # Return zero-cost usage object as fallback
            return LLMUsage(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                input_cost=Decimal('0'),
                output_cost=Decimal('0'),
                total_cost=Decimal('0'),
                request_timestamp=datetime.now(timezone.utc)
            )
    
    def calculate_google_api_cost(
        self, 
        queries_made: int, 
        total_results_returned: int,
        api_calls_count: Optional[int] = None
    ) -> GoogleAPIUsage:
        """
        Calculate Google Custom Search API costs
        
        Args:
            queries_made: Number of search queries performed
            total_results_returned: Total number of results returned
            api_calls_count: Number of actual API calls made (may be different from queries)
            
        Returns:
            GoogleAPIUsage object with detailed cost breakdown
        """
        try:
            # API calls count defaults to queries made
            if api_calls_count is None:
                api_calls_count = queries_made
            
            # Calculate cost per query
            cost_per_query = self.GOOGLE_SEARCH_COST_PER_1000_QUERIES / Decimal('1000')
            
            # Calculate total cost (assuming all queries are billable for simplicity)
            # In reality, first 100 queries per day are free, but tracking daily limits 
            # would require persistent storage
            total_cost = Decimal(queries_made) * cost_per_query
            total_cost = total_cost.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            cost_per_query = cost_per_query.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            
            usage = GoogleAPIUsage(
                queries_made=queries_made,
                total_results_returned=total_results_returned,
                api_calls_count=api_calls_count,
                cost_per_query=cost_per_query,
                total_cost=total_cost,
                request_timestamp=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"Google API cost calculated: {queries_made} queries = ${total_cost}")
            return usage
            
        except Exception as e:
            self.logger.error(f"Error calculating Google API cost: {e}")
            # Return zero-cost usage object as fallback
            return GoogleAPIUsage(
                queries_made=queries_made,
                total_results_returned=total_results_returned,
                api_calls_count=api_calls_count or queries_made,
                cost_per_query=Decimal('0'),
                total_cost=Decimal('0'),
                request_timestamp=datetime.now(timezone.utc)
            )
    
    def format_cost_for_display(self, cost: Decimal) -> str:
        """
        Format cost for user-friendly display
        
        Args:
            cost: Cost as Decimal
            
        Returns:
            Formatted cost string (e.g., "$0.0123", "$1.25")
        """
        if cost == 0:
            return "$0.00"
        elif cost < Decimal('0.01'):
            return f"${cost:.4f}"
        else:
            return f"${cost:.2f}"
    
    def get_cost_summary(self, llm_usage: LLMUsage, google_usage: GoogleAPIUsage) -> Dict[str, Any]:
        """
        Generate a comprehensive cost summary for reporting
        
        Args:
            llm_usage: LLM usage data
            google_usage: Google API usage data
            
        Returns:
            Dictionary with formatted cost summary
        """
        total_cost = llm_usage.total_cost + google_usage.total_cost
        
        return {
            "llm_usage": {
                "model": llm_usage.model,
                "input_tokens": llm_usage.input_tokens,
                "output_tokens": llm_usage.output_tokens,
                "total_tokens": llm_usage.total_tokens,
                "input_cost": self.format_cost_for_display(llm_usage.input_cost),
                "output_cost": self.format_cost_for_display(llm_usage.output_cost),
                "total_cost": self.format_cost_for_display(llm_usage.total_cost),
                "cost_per_1k_tokens": self.format_cost_for_display(
                    (llm_usage.total_cost / Decimal(llm_usage.total_tokens)) * Decimal('1000') 
                    if llm_usage.total_tokens > 0 else Decimal('0')
                )
            },
            "google_api_usage": {
                "queries_made": google_usage.queries_made,
                "api_calls": google_usage.api_calls_count,
                "results_returned": google_usage.total_results_returned,
                "cost_per_query": self.format_cost_for_display(google_usage.cost_per_query),
                "total_cost": self.format_cost_for_display(google_usage.total_cost)
            },
            "total_cost": self.format_cost_for_display(total_cost),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }