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
        prompt = f"""Write exactly ONE humorous message that starts with "<!channel> Kudo rain for @{user_name}" followed by a playful roast with pop culture references.

Requirements:
- Start with "<!channel> Kudo rain for @{user_name}"
- One sentence only, 40-60 words
- Playfully sarcastic about {user_title} work habits
- Use 1-2 DIVERSE pop culture references (do not stick to Marvel/DC heroes every time)
- Workplace appropriate but cheeky
- Return ONLY the message, no alternatives or explanations

Examples of style:
"<!channel> Kudo rain for @alex - like Hermione with a time-turner, somehow everywhere at once, but your real superpower is turning 30-min meetings into Groundhog Day!"
- "<!channel> Kudo rain for @alex - like Hermione Granger with a time-turner, you're somehow everywhere at once, though your real
superpower is making simple meetings feel like Groundhog Day!"
- "<!channel> Kudo rain for @sam - channeling your inner Gordon Ramsay in code reviews and Bob Ross in debugging, you're a walking
contradiction who somehow makes it work!"
- "<!channel> Kudo rain for @jamie - like Sherlock Holmes solving mysteries, you find bugs nobody else can see, but unlike him you
still get lost in your own directory structure!"
- "<!channel> Kudo rain for @thomas - like Thanos wiped out half of all life with a snap of his fingers (let's not mention the
deletion of half of the database)"

Create something FRESH and ORIGINAL with different references.

Write exactly one message:"""

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

            if message.content and len(message.content) > 0:
                return message.content[0].text.strip()
            else:
                return self._fallback_message(user_name, user_title)

        except Exception as e:
            print(f"❌ Error generating kudo rain: {e}")
            return self._fallback_message(user_name, user_title)

    def _fallback_message(self, user_name: str, user_title: str = "Developer") -> str:
        """Generate a simple fallback message if AI fails."""
        return f"<!channel> Kudo rain for @{user_name} - like a superhero {user_title} whose only power is making coffee disappear and Zoom calls awkward! 🎯☕"

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
