import json
import logging
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
import os

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

# We assume GEMINI_API_KEY is in the environment
client = genai.Client()

def generate_text(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """Generates plain text output."""
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text

def generate_json(prompt: str, response_schema: Type[T], model_name: str = "gemini-2.5-flash") -> T:
    """Generates JSON output validated against a Pydantic model with one retry."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.2
    )
    
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            # Try to parse and validate
            parsed = json.loads(response.text)
            return response_schema.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Attempt {attempt + 1} failed for generate_json: {e}")
            if attempt == 1:
                raise ValueError("Failed to generate valid JSON after retries.") from e
    
    raise ValueError("Unexpected error in generate_json")
