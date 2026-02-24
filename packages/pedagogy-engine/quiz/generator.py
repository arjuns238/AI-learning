import os
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from quiz.schema import EnhancedQuiz
from layer1.schema import PedagogicalIntentWithMetadata

load_dotenv()

QUIZ_PROMPT = """
You are generating a conceptual multiple-choice quiz.

Topic: {topic}

Pedagogical intent (authoritative source of truth):
{intent_json}

Rules:
- Questions must test conceptual understanding, not trivia
- All correct answers must be derivable from this intent
- Include strong distractors based on likely misconceptions
- Provide a short explanation for the correct answer
- Prefer grounding questions in specific sections

Return ONLY valid JSON matching this schema:
{schema}
"""


class QuizGenerator:
    """Generates conceptual multiple-choice quizzes from pedagogical intent."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_provider: Optional[str] = None,
        temperature: float = 0.7
    ):
        # Determine default model first
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL")
            if model_name is None:
                model_name = "gpt-4o-mini" if api_provider != "anthropic" else "claude-opus-4-5"
        self.model_name = model_name

        # Infer API provider from model name if not explicitly provided
        if api_provider is None:
            if self.model_name.startswith("gpt") or self.model_name.startswith("o1"):
                api_provider = "openai"
            elif self.model_name.startswith("claude"):
                api_provider = "anthropic"
            else:
                api_provider = os.getenv("API_PROVIDER", "openai")
        
        self.api_provider = api_provider
        self.temperature = temperature

        # Initialize API client
        if self.api_provider == "openai":
            self._init_openai()
        elif self.api_provider == "anthropic":
            self._init_anthropic()
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")

    def _init_openai(self):
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=api_key)

    def _init_anthropic(self):
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_openai(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=4096,
            response_format={"type": "json_object"} if "gpt-" in self.model_name else None
        )
        return resp.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=4096
        )
        return resp.content[0].text

    def _call_api(self, prompt: str) -> str:
        if self.api_provider == "openai":
            return self._call_openai(prompt)
        elif self.api_provider == "anthropic":
            return self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")

    def _build_prompt(self, intent: PedagogicalIntentWithMetadata) -> str:
        """Fill in the QUIZ_PROMPT with topic, intent, and schema."""
        return QUIZ_PROMPT.format(
            topic=intent.intent.topic,
            intent_json=intent.model_dump_json(indent=2),
            schema=EnhancedQuiz.model_json_schema()
        )

    def _parse_response(self, response_text: str) -> EnhancedQuiz:
        """Parse JSON from LLM response, stripping code blocks if needed."""
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()

        return EnhancedQuiz.model_validate_json(json_text)

    def generate(self, intent: PedagogicalIntentWithMetadata) -> EnhancedQuiz:
        prompt = self._build_prompt(intent)
        response_text = self._call_api(prompt)
        return self._parse_response(response_text)
