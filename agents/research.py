"""
Research Agent - Finds content opportunities
"""
import os
import json
from typing import Dict, Any, List
from supabase import Client

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
except:
    pass

class ResearchAgent:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research content opportunities"""
        topic = input_data.get('topic', '')
        keywords = input_data.get('keywords', [])
        
        # Get existing content to find gaps
        existing = self._get_existing_content()
        
        # Generate research
        research = await self._research_topic(topic, keywords, existing)
        
        return research
    
    def _get_existing_content(self) -> List[str]:
        """Get existing topics to avoid duplicates"""
        try:
            result = self.supabase.table('drafts').select('title').execute()
            return [d.get('title', '') for d in result.data]
        except:
            return []
    
    async def _research_topic(self, topic: str, keywords: List[str], existing: List[str]) -> dict:
        """AI research"""
        
        prompt = f"""Research content opportunities for Broward Health about: {topic}

Existing topics to avoid: {', '.join(existing[:10])}
Keywords: {', '.join(keywords)}

Provide 3 content ideas with:
1. Specific title
2. Primary keyword
3. Content angle
4. Target services to link

Format as JSON:
{{
  "topics": [
    {{
      "title": "...",
      "primary_keyword": "...",
      "content_angle": "...",
      "target_services": ["..."]
    }}
  ]
}}"""
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500
                )
                content = response.choices[0].message.content
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0:
                    return json.loads(content[start:end])
            except:
                pass
        
        return {"topics": [{"title": topic, "primary_keyword": keywords[0] if keywords else topic, "content_angle": "General overview", "target_services": ["General Medicine"]}]}
