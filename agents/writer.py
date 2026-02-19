"""
Writer Agent - Generates healthcare blog content
Based on OPTIMIZED prompts from AGENT-OPTIMIZATION-STRATEGY.md
"""
import os
import json
import re
from typing import Dict, Any, Optional
from supabase import Client

# Use OpenAI or MiniMax
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
except:
    pass

class WriterAgent:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a blog post"""
        topic = input_data['topic']
        category_id = input_data['category_id']
        keywords = input_data.get('keywords', [])
        
        # Build the optimized prompt
        prompt = self._build_prompt(topic, keywords)
        
        # Call AI
        response = await self._call_ai(prompt)
        
        # Parse response
        parsed = self._parse_output(response)
        
        # Save to database
        draft_id = self._save_draft(category_id, parsed, topic)
        
        return {
            'draft_id': draft_id,
            'title': parsed.get('title', topic),
            'sections': parsed.get('sections', []),
            'word_count': parsed.get('word_count', 0),
            'status': 'draft created'
        }
    
    def _build_prompt(self, topic: str, keywords: list) -> str:
        """Build the optimized prompt from AGENT-OPTIMIZATION-STRATEGY.md"""
        return f"""Write a comprehensive healthcare blog post for Broward Health that EXCEEDS their published content quality.

Topic: {topic}
Keywords: {', '.join(keywords)}

REQUIREMENTS (from optimization strategy):
- 2,000-4,000 words
- 10-15 detailed H2 sections
- Each section: 3-5 paragraphs (NOT summaries)
- Expert but accessible tone (like Dr. Jason Walters)
- South Florida context throughout
- Actionable advice in every section
- Medical disclaimer required
- CTA to Broward Health services
- FAQ section (3-5 questions)
- "Reviewed by Dr. [Name]" placeholder for doctor

Target quality: Match or beat https://www.browardhealth.org/blogs/preventing-sports-injuries-tips-for-athletes-of-all-levels

Format as JSON:
{{
  "title": "Clear, actionable title",
  "slug": "url-friendly-slug",
  "intro": {{
    "hook": "Compelling opening",
    "problem": "What readers learn",
    "preview": "What article covers"
  }},
  "sections": [
    {{
      "h2": "Section Title",
      "paragraphs": ["para 1", "para 2", "para 3"]
    }}
  ],
  "conclusion": {{
    "summary": "Key takeaways",
    "cta": "Schedule appointment"
  }},
  "faq": [{{"question": "?", "answer": "?"}}],
  "medical_disclaimer": "Standard disclaimer",
  "word_count": 2500
}}"""
    
    async def _call_ai(self, prompt: str) -> str:
        """Call AI model - supports OpenAI or MiniMax"""
        
        # Try OpenAI first
        if os.getenv("OPENAI_API_KEY"):
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=6000
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI failed: {e}")
        
        # Fallback to MiniMax
        try:
            import requests
            response = requests.post(
                "https://api.minimax.chat/v1/text/chatcompletion_pro",
                headers={
                    "Authorization": f"Bearer {os.getenv('MINIMAX_API_KEY', '')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "MiniMax-Text-01",
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 6000
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"MiniMax failed: {e}")
        
        raise Exception("No AI API available")
    
    def _get_system_prompt(self) -> str:
        """OPTIMIZED system prompt from AGENT-OPTIMIZATION-STRATEGY.md"""
        return """You are a Senior Medical Health Writer for Broward Health, a leading hospital in South Florida. Your writing matches or EXCEEDS Dr. Jason Walters' quality.

STRICT REQUIREMENTS:
1. WORD COUNT: 2,000-4,000 words
2. SECTIONS: 10-15 H2 sections, each with 3-5 paragraphs
3. TONE: Expert yet accessible
4. LOCAL: Reference South Florida/Broward County
5. ACTIONABLE: Advice in every section
6. DISCLAIMER: Include medical disclaimer
7. CTA: Link to Broward Health services

QUALITY CHECKS:
□ Word count ≥ 2,000
□ At least 10 H2 sections
□ Each section 2+ paragraphs
□ Local relevance
□ No unverified medical claims

Output ONLY valid JSON."""
    
    def _parse_output(self, content: str) -> dict:
        """Parse JSON from AI response"""
        try:
            # Find JSON in response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Return fallback structure
        return {
            "title": "Generated Article",
            "slug": "generated-article",
            "intro": {"hook": "", "problem": "", "preview": ""},
            "sections": [],
            "conclusion": {"summary": "", "cta": ""},
            "faq": [],
            "medical_disclaimer": "This content is for informational purposes only.",
            "word_count": 0
        }
    
    def _save_draft(self, category_id: str, parsed: dict, topic: str) -> str:
        """Save draft to Supabase"""
        
        # Build full content
        content = ""
        if parsed.get('intro', {}).get('problem'):
            content += parsed['intro']['problem'] + "\n\n"
        if parsed.get('intro', {}).get('preview'):
            content += parsed['intro']['preview'] + "\n\n"
        
        for section in parsed.get('sections', []):
            content += f"## {section.get('h2', '')}\n\n"
            for para in section.get('paragraphs', []):
                content += f"{para}\n\n"
        
        if parsed.get('conclusion', {}).get('summary'):
            content += f"## Conclusion\n\n{parsed['conclusion']['summary']}\n\n"
        if parsed.get('conclusion', {}).get('cta'):
            content += f"**{parsed['conclusion']['cta']}**\n\n"
        
        # Add FAQ
        if parsed.get('faq'):
            content += "## Frequently Asked Questions\n\n"
            for faq in parsed['faq']:
                content += f"**{faq.get('question', '')}**\n{faq.get('answer', '')}\n\n"
        
        # Add disclaimer
        content += f"\n---\n{parsed.get('medical_disclaimer', '')}"
        
        # Generate slug
        title = parsed.get('title', topic)
        slug = self._generate_slug(title)
        
        # Save to Supabase
        result = self.supabase.table('drafts').insert({
            'title': title,
            'slug': slug,
            'category_id': category_id,
            'content': content,
            'excerpt': parsed.get('intro', {}).get('preview', '')[:200],
            'meta_description': parsed.get('intro', {}).get('preview', '')[:160],
            'workflow_status': 'ai_review',
            'seo_score': 0,
            'llm_score': 0,
            'read_time_minutes': max(5, (parsed.get('word_count', 2000) // 200))
        }).execute()
        
        draft_id = result.data[0]['id']
        
        # Save sections
        for i, section in enumerate(parsed.get('sections', [])):
            self.supabase.table('draft_sections').insert({
                'draft_id': draft_id,
                'h2': section.get('h2', ''),
                'content': '\n\n'.join(section.get('paragraphs', [])),
                'order_index': i
            }).execute()
        
        return draft_id
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return f"/blogs/{slug}"
