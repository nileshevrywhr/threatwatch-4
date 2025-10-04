"""
Fallback LLM integration for production deployment
Used when emergentintegrations package is not available
"""
import os
import json
import httpx
import asyncio
from typing import Optional, Dict, Any


class LLMFallback:
    """Fallback LLM client for production deployment"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        self.base_url = "https://api.openai.com/v1"  # Fallback to OpenAI directly
        
    async def send_message(self, message: str) -> str:
        """Send message to LLM and return response"""
        if not self.api_key:
            return "LLM service not configured - using mock response for threat analysis."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity analyst providing threat intelligence analysis."
                    },
                    {
                        "role": "user", 
                        "content": message
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"LLM API Error {response.status_code}: Using fallback analysis."
                    
        except Exception as e:
            print(f"LLM Error: {e}")
            return "LLM service temporarily unavailable - using fallback threat analysis."


class UserMessage:
    """Compatibility class for emergentintegrations UserMessage"""
    
    def __init__(self, text: str):
        self.text = text


class LlmChat:
    """Compatibility class for emergentintegrations LlmChat"""
    
    def __init__(self, **kwargs):
        self.llm_fallback = LLMFallback()
        
    async def send_message(self, message: UserMessage) -> str:
        """Send message using fallback implementation"""
        return await self.llm_fallback.send_message(message.text)


# Mock function to maintain compatibility
def get_llm_key() -> Optional[str]:
    """Get LLM API key from environment"""
    return os.getenv('EMERGENT_LLM_KEY')