from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException

@dataclass
class PromptTemplate:
    template_id: str
    version: str
    system_prompt: str
    user_prompt_template: str
    name: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    is_active: bool = True

class PromptManager:
    """
    Versioned, Provider-Independent Prompt Registry with Variable Interpolation
    and strict Domain Policy Guardrails (No medical or insurance prompts allowed).
    """
    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        # 1. Structural Reasoning Template
        self.register(PromptTemplate(
            template_id="generic_reasoning",
            version="1.0.0",
            name="Generic Structural Reasoning",
            description="Provider-independent template for structured step-by-step logical reasoning",
            system_prompt="You are an autonomous AI assistant executing structured contextual reasoning.",
            user_prompt_template="Context:\n{context}\n\nTask Query:\n{query}",
            tags=["reasoning", "general"],
            variables=["context", "query"]
        ))

        # 2. JSON Extraction Template
        self.register(PromptTemplate(
            template_id="json_extractor",
            version="1.0.0",
            name="JSON Schema Data Extractor",
            description="Extracts structured JSON payload from unstructured text according to schema",
            system_prompt="You are a strict JSON data extraction engine. Respond strictly with valid JSON.",
            user_prompt_template="Target JSON Schema:\n{schema}\n\nUnstructured Input Text:\n{input_text}",
            tags=["json", "extraction"],
            variables=["schema", "input_text"]
        ))

        # 3. Text Summarizer Template
        self.register(PromptTemplate(
            template_id="text_summarizer",
            version="1.0.0",
            name="Contextual Text Summarizer",
            description="Generates concise bulleted summaries of lengthy input text",
            system_prompt="You are an expert summarizer. Synthesize input text into key concise takeaways.",
            user_prompt_template="Input Document:\n{document}\n\nSummary Length Constraint:\n{max_bullets} key points.",
            tags=["summarization", "nlp"],
            variables=["document", "max_bullets"]
        ))

    def register(self, template: PromptTemplate) -> None:
        """
        Registers a prompt template into the registry after validating domain guardrails.
        Rejects any template containing medical or insurance instructions.
        """
        # Validate system prompt
        domain_guardrail.enforce_policy(template.system_prompt, context_name=f"Template '{template.template_id}' System Prompt")
        # Validate user prompt template
        domain_guardrail.enforce_policy(template.user_prompt_template, context_name=f"Template '{template.template_id}' User Template")

        key = f"{template.template_id}:{template.version}"
        self._templates[key] = template

    def get(self, template_id: str, version: str = "1.0.0") -> Optional[PromptTemplate]:
        key = f"{template_id}:{version}"
        return self._templates.get(key)

    def list_templates(self, tag: Optional[str] = None) -> List[PromptTemplate]:
        templates = list(self._templates.values())
        if tag:
            templates = [t for t in templates if tag in t.tags]
        return templates

    def render(self, template_id: str, version: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        Renders a prompt template with provided variables and enforces domain policy on rendered output.
        """
        key = f"{template_id}:{version}"
        template = self._templates.get(key)
        if not template:
            raise ValueError(f"Prompt template '{key}' not found in registry.")

        rendered_user_prompt = template.user_prompt_template.format(**variables)

        # Enforce policy on final rendered output
        domain_guardrail.enforce_policy(template.system_prompt, context_name=f"Rendered System Prompt ('{key}')")
        domain_guardrail.enforce_policy(rendered_user_prompt, context_name=f"Rendered User Prompt ('{key}')")

        return {
            "system_prompt": template.system_prompt,
            "user_prompt": rendered_user_prompt,
            "template_id": template_id,
            "version": version
        }

    def delete_template(self, template_id: str, version: str) -> bool:
        key = f"{template_id}:{version}"
        if key in self._templates:
            del self._templates[key]
            return True
        return False

prompt_manager = PromptManager()
