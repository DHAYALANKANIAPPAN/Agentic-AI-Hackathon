import json
import logging
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

# Initialize OpenAI Client for NVIDIA NIM
from openai import OpenAI
import openai

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = os.environ.get("NVIDIA_API_KEY", "missing_key")
)

def generate_text(prompt: str, model_name: str = "meta/llama-3.2-11b-vision-instruct") -> str:
    """Generates plain text output."""
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except openai.APIError as e:
            logger.warning(f"API Error in text (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)

def generate_json(prompt: str, response_schema: Type[T], model_name: str = "meta/llama-3.2-11b-vision-instruct") -> T:
    """Generates JSON output validated against a Pydantic model with retries."""
    import time
    
    schema_json = json.dumps(response_schema.model_json_schema())
    
    # Inject the schema requirement into the prompt for NIM
    system_prompt = (
        "You are a helpful JSON-generating assistant. "
        "You must respond ONLY with a valid JSON object. "
        "The JSON object must strictly conform to this JSON Schema:\n"
        f"{schema_json}\n\n"
        "Do not include any markdown formatting, backticks, or extra text. Just the JSON."
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Try to parse and validate
            raw_text = response.choices[0].message.content
            
            # Clean markdown formatting if the model included it
            if raw_text.strip().startswith("```json"):
                raw_text = raw_text.strip()[7:]
            if raw_text.strip().startswith("```"):
                raw_text = raw_text.strip()[3:]
            if raw_text.strip().endswith("```"):
                raw_text = raw_text.strip()[:-3]
            raw_text = raw_text.strip()
            
            parsed = json.loads(raw_text)
            return response_schema.model_validate(parsed)
            
        except openai.APIError as e:
            logger.warning(f"API Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise ValueError("API is currently unavailable after multiple retries.") from e
            time.sleep(2)
            
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Parsing Error (Attempt {attempt + 1}/{max_retries}): {e}")
            logger.warning(f"RAW TEXT: {raw_text}")
            if attempt == max_retries - 1:
                raise ValueError("Failed to generate valid JSON after retries.") from e
                
    raise ValueError("Unexpected error in generate_json")
