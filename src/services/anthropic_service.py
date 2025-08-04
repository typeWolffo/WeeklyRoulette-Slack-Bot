"""Anthropic AI service for generating humorous kudo rain messages."""

import os
from typing import Optional

import anthropic


class AnthropicService:
    """Service for generating AI-powered humorous messages using Claude."""

    def __init__(self):
        """Initialize the Anthropic client."""
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    async def generate_kudo_rain(self, user_name: str, user_title: str = "Developer") -> str:
        """
        Generate a humorous kudo rain message for the selected user.

        Args:
            user_name: The display name of the selected user
            user_title: The job title of the selected user

        Returns:
            A humorous one-sentence kudo rain message
        """
        prompt = f"""Create a humorous, one-sentence roast that starts with '@channel Kudo rain for {user_name}' (who works as {user_title}) followed by pop culture references, but make it more teasing and sarcastic while still being workplace appropriate.

IMPORTANT: Use DIVERSE pop culture references. Avoid overused ones like Doctor Strange, Neo, Batman, Superman. Be creative!

Make it:
- One sentence only
- More sarcastic and teasing (but not cruel)
- Include 1-2 DIFFERENT pop culture references each time
- Focus more on the roast than the praise
- Around 40-60 words maximum
- Use humor that gently calls out common workplace quirks (especially related to their role as {user_title})

Example styles (use DIFFERENT references):
- "Kudo rain for @alex - like Hermione Granger with a time-turner, you're somehow everywhere at once, though your real superpower is making simple meetings feel like Groundhog Day!"
- "Kudo rain for @sam - channeling your inner Gordon Ramsay in code reviews and Bob Ross in debugging, you're a walking contradiction who somehow makes it work!"
- "Kudo rain for @jamie - like Sherlock Holmes solving mysteries, you find bugs nobody else can see, but unlike him you still get lost in your own directory structure!"
- "Kudo rain for @thomas - like Thanos wiped out half of all life with a snap of his fingers (let's not mention the deletion of half of the database)"

Create something FRESH and ORIGINAL with different references:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                temperature=0.8,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract the text content from the response
            if message.content and len(message.content) > 0:
                return message.content[0].text.strip()
            else:
                return self._fallback_message(user_name, user_title)

        except Exception as e:
            print(f"❌ Error generating kudo rain: {e}")
            return self._fallback_message(user_name, user_title)

    def _fallback_message(self, user_name: str, user_title: str = "Developer") -> str:
        """Generate a simple fallback message if AI fails."""
        return f"Kudo rain for {user_name} - like a superhero {user_title} whose only power is making coffee disappear and Zoom calls awkward! 🎯☕"

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
