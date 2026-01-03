from openai import OpenAI
from io import BytesIO
from PIL import Image
import requests
import logging
from typing import List, Dict, Union, Optional

class OpenaiAPI:

    def __init__(self, **kwargs):
        self.client = OpenAI(api_key=kwargs.get('api_key'))
        self.model = kwargs.get('model', 'gpt-4o')
        self.temperature = kwargs.get('temperature', 0.3)
        self.max_tokens = kwargs.get('max_tokens', 3000)

    def _flatten_messages(self, messages: Union[str, List[Dict[str, str]]]) -> str:
        """Best-effort conversion of a chat messages list into a single input string."""
        if isinstance(messages, str):
            return messages
        try:
            return "\n\n".join(
                f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in messages
            )
        except Exception:
            return str(messages)

    def _to_responses_input(self, messages: Union[str, List[Dict[str, str]]]):
        """Convert chat-style messages to Responses API input format with typed content."""
        if isinstance(messages, str):
            return messages
        try:
            normalized: List[Dict[str, Union[str, List[Dict[str, str]]]]] = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if isinstance(content, list):
                    # Assume already in typed content form
                    normalized.append({"role": role, "content": content})
                else:
                    normalized.append(
                        {"role": role, "content": [{"type": "input_text", "text": str(content)}]}
                    )
            return normalized
        except Exception:
            # Fallback: best-effort flattening
            return self._flatten_messages(messages)
    def _has_responses_api(self) -> bool:
        return hasattr(self.client, "responses")

    def generate_response(self, messages: Union[str, List[Dict[str, str]]]) -> Optional[str]:
        try:
            # Route GPT-5 models to the Responses API
            if str(self.model).startswith("gpt-5"):
                if self._has_responses_api():
                    # Use a single flattened string as input for best compatibility
                    input_payload = self._flatten_messages(messages)
                    resp = self.client.responses.create(
                        model=self.model,
                        input=input_payload,
                        temperature=1,
                        reasoning={"effort": "low"},
                        max_output_tokens=self.max_tokens,
                    )

                    # Prefer the convenience property when available
                    text = getattr(resp, "output_text", None)

                    # Fallback: assemble text from the structured output fields
                    if not text:
                        try:
                            outputs = getattr(resp, "output", None) or getattr(resp, "outputs", None)
                            if outputs:
                                parts: List[str] = []
                                for out in outputs:
                                    content = getattr(out, "content", None)
                                    if content:
                                        for c in content:
                                            t = getattr(c, "text", None)
                                            if t:
                                                parts.append(t)
                                if parts:
                                    text = "\n".join(parts)
                        except Exception:
                            pass

                    # Deep-search any 'text' fields in the serialized object as a last resort
                    if not text:
                        try:
                            raw = resp.model_dump() if hasattr(resp, "model_dump") else getattr(resp, "__dict__", None) or resp
                            parts: List[str] = []
                            def _collect(obj):
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        if k == "text" and isinstance(v, str):
                                            parts.append(v)
                                        else:
                                            _collect(v)
                                elif isinstance(obj, list):
                                    for it in obj:
                                        _collect(it)
                            _collect(raw)
                            if parts:
                                text = "\n".join(parts)
                        except Exception:
                            pass

                    # Log raw payload to help diagnose schema changes
                    if not text:
                        try:
                            raw_json = resp.model_dump_json() if hasattr(resp, "model_dump_json") else str(resp)
                            logging.info(f"Responses API raw: {raw_json}")
                        except Exception:
                            pass

                    if not text:
                        # Fallback to Chat Completions for GPT-5 with correct params
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages if isinstance(messages, list) else [{"role": "user", "content": str(messages)}],
                            temperature=1,
                            extra_body={
                                "max_completion_tokens": self.max_tokens,
                                "reasoning": {"effort": "low"},
                            },
                        )
                        content = (response.choices[0].message.content or "").strip()
                        if not content:
                            try:
                                logging.info(
                                    "OpenAI fallback Chat returned empty content. finish_reason=%s",
                                    getattr(response.choices[0], "finish_reason", None),
                                )
                                logging.info("OpenAI fallback Chat raw: %s", response.model_dump_json())
                            except Exception:
                                pass
                            return None
                        logging.info(f"Generated answer (fallback Chat): {content}")
                        return content

                    logging.info(f"Generated answer: {text}")
                    return text.strip()
                else:
                    # SDK lacks Responses API; use Chat Completions with GPT-5 params via extra_body
                    # Explicitly set temperature=1 (only default supported by GPT-5 on Chat)
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages if isinstance(messages, list) else [{"role": "user", "content": str(messages)}],
                        temperature=1,
                        extra_body={
                            "max_completion_tokens": self.max_tokens,
                            "reasoning": {"effort": "low"},
                        },
                    )
                    content = (response.choices[0].message.content or "").strip()
                    if not content:
                        try:
                            logging.info(
                                "OpenAI Chat returned empty content. finish_reason=%s",
                                getattr(response.choices[0], "finish_reason", None),
                            )
                            logging.info("OpenAI Chat raw: %s", response.model_dump_json())
                        except Exception:
                            pass
                        return None
                    logging.info(f"Generated answer: {content}")
                    return content

            # Default path for non-GPT-5 models: Chat Completions API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages if isinstance(messages, list) else [{"role": "user", "content": str(messages)}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                try:
                    logging.info(
                        "OpenAI Chat returned empty content. finish_reason=%s",
                        getattr(response.choices[0], "finish_reason", None),
                    )
                    logging.info("OpenAI Chat raw: %s", response.model_dump_json())
                except Exception:
                    pass
                return None
            logging.info(f"Generated answer: {content}")
            return content
        except Exception as e:
            logging.error(f"OpenAI generate_response error: {e}")
            return None

    def generate_image(self, prompt: str, model: str = "dall-e-3") -> Optional[Image.Image]:
        # https://github.com/openai/openai-python/blob/main/examples/picture.py
        try:
            # Use the instantiated client for Images API to ensure API key is applied
            img_resp = self.client.images.generate(prompt=prompt, model=model)
            # Download the image
            img_url = img_resp.data[0].url
            response = requests.get(img_url)
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            logging.error(f"OpenAI generate_image error: {e}")
            return None
