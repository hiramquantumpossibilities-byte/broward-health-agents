"""
Image Agent - Generates/captions images for blog posts
Based on OPTIMIZED prompts from AGENT-OPTIMIZATION-STRATEGY.md
"""
import os
import json
from typing import Dict, Any
from supabase import Client

try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY", "")
except:
    pass

class ImageAgent:
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or fetch image for draft"""
        draft_id = input_data.get('draft_id')
        title = input_data.get('title', '')
        topic = input_data.get('topic', '')
        
        # Generate image (using DALL-E if available)
        image_result = await self._generate_image(title, topic)
        
        # Update draft
        if draft_id:
            self.supabase.table('drafts').update({
                'hero_image_url': image_result.get('url', ''),
                'updated_at': 'now()'
            }).eq('id', draft_id).execute()
        
        return image_result
    
    async def _generate_image(self, title: str, topic: str) -> dict:
        """Generate hero image using DALL-E"""
        
        prompt = f"""Generate a professional medical illustration for a Broward Health blog post.

Blog Title: {title}

REQUIREMENTS:
- Clean, modern healthcare aesthetic
- Broward Health brand colors: Blue (#005EB8), white, teal
- No text
- Photorealistic but approachable
- South Florida healthcare setting
- Suitable for hospital website
- 1792x1024 aspect ratio"""
        
        # Try DALL-E
        if os.getenv("OPENAI_API_KEY"):
            try:
                response = openai.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1792x1024",
                    quality="standard",
                    n=1
                )
                return {
                    "url": response.data[0].url,
                    "alt_text": f"Healthcare illustration for: {title}",
                    "source": "dalle"
                }
            except Exception as e:
                print(f"Image generation failed: {e}")
        
        # Fallback - return placeholder
        return {
            "url": "",
            "alt_text": f"Healthcare image for: {title}",
            "source": "none",
            "note": "Configure OPENAI_API_KEY for image generation"
        }
