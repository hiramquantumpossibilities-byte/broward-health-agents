"""
SEO Agent - Optimizes content for search engines
Based on OPTIMIZED prompts from AGENT-OPTIMIZATION-STRATEGY.md
"""
import os
import json
import re
from typing import Dict, Any
from supabase import Client

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
except:
    pass

class SEOAgent:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize draft for SEO"""
        draft_id = input_data.get('draft_id')
        
        # Get draft
        draft = self.supabase.table('drafts').select('*').eq('id', draft_id).execute()
        if not draft.data:
            raise Exception("Draft not found")
        
        draft_data = draft.data[0]
        
        # Run SEO optimization
        seo_result = await self._optimize_seo(draft_data)
        
        # Update draft with SEO data
        update_data = {
            'meta_description': seo_result.get('meta_description', ''),
            'seo_score': seo_result.get('seo_score', 0),
            'updated_at': 'now()'
        }
        
        self.supabase.table('drafts').update(update_data).eq('id', draft_id).execute()
        
        # Add quality gate
        self.supabase.table('quality_gates').insert({
            'request_id': draft_id,
            'gate_name': 'seo_score',
            'passed': seo_result.get('seo_score', 0) >= 80,
            'value': {'score': seo_result.get('seo_score', 0)},
            'threshold': {'min': 80}
        }).execute()
        
        return seo_result
    
    async def _optimize_seo(self, draft: dict) -> dict:
        """Call AI to optimize SEO"""
        prompt = f"""Analyze and optimize this blog post for SEO:

Title: {draft['title']}
Content: {draft['content'][:3000]}

Provide SEO optimization:
1. Title tag (50-60 chars)
2. Meta description (150-160 chars, include CTA)
3. URL slug (/blogs/...)
4. Internal link suggestions (3-5 Broward Health pages)
5. SEO score (0-100)

Format as JSON:
{{
  "title_tag": "...",
  "meta_description": "...",
  "url_slug": "/blogs/...",
  "internal_links": [{{"text": "...", "url": "/..."}}],
  "seo_score": 85
}}"""
        
        # Try OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                content = response.choices[0].message.content
                
                # Parse JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0:
                    return json.loads(content[start:end])
            except Exception as e:
                print(f"SEO optimization failed: {e}")
        
        # Fallback - calculate basic score
        return self._calculate_basic_seo(draft)
    
    def _get_system_prompt(self) -> str:
        """OPTIMIZED prompt from AGENT-OPTIMIZATION-STRATEGY.md"""
        return """You are a Healthcare SEO Specialist for Broward Health.

REQUIRED OPTIMIZATIONS:
1. TITLE TAG: 50-60 chars, primary keyword at front
2. META DESCRIPTION: 150-160 chars, actionable, include keyword + CTA
3. URL SLUG: Clean, hyphenated, starts with /blogs/
4. INTERNAL LINKS: 3-5 links to Broward Health service pages
5. SEO SCORE: 0-100 based on optimization

Output ONLY valid JSON."""
    
    def _calculate_basic_seo(self, draft: dict) -> dict:
        """Calculate basic SEO score without AI"""
        title = draft.get('title', '')
        content = draft.get('content', '')
        
        score = 50
        
        # Title length
        if 30 <= len(title) <= 60:
            score += 10
        
        # Has meta description placeholder
        if draft.get('meta_description'):
            score += 10
        
        # Content length
        if len(content) > 1500:
            score += 15
        if len(content) > 2500:
            score += 10
        
        # Has sections
        if '## ' in content:
            score += 5
        
        return {
            'title_tag': title[:60],
            'meta_description': f"Learn about {title}. Expert care at Broward Health.",
            'url_slug': f"/blogs/{title.lower().replace(' ', '-')[:50]}",
            'internal_links': [
                {"text": "Broward Health Services", "url": "/services"},
                {"text": "Schedule Appointment", "url": "/appointment"}
            ],
            'seo_score': min(score, 100)
        }
