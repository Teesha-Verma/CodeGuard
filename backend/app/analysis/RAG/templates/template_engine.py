from pydantic import BaseModel, Field
from typing import Dict, Tuple, List

class PromptTemplate(BaseModel):
    """Template for generating a prompt."""
    name: str = Field(description="Name of the template")
    system_instructions: str = Field(description="System instructions for the model")
    required_sections: List[str] = Field(default_factory=list, description="List of required context blocks")
    output_format_spec: str = Field(description="Specification for the output format")

class TemplateEngine:
    """Engine for retrieving and rendering templates."""
    
    def __init__(self):
        self._templates = {
            "security_review": PromptTemplate(
                name="security_review",
                system_instructions="You are an expert security reviewer. Analyze the code for vulnerabilities.",
                required_sections=["code_context", "vulnerabilities"],
                output_format_spec="{format_instructions}"
            ),
            "performance_review": PromptTemplate(
                name="performance_review",
                system_instructions="You are an expert performance reviewer. Identify bottlenecks and optimization opportunities.",
                required_sections=["code_context", "performance_metrics"],
                output_format_spec="{format_instructions}"
            ),
            "architecture_review": PromptTemplate(
                name="architecture_review",
                system_instructions="You are an expert software architect. Evaluate the design patterns, scalability, and maintainability.",
                required_sections=["repo_context", "code_context"],
                output_format_spec="{format_instructions}"
            ),
            "code_quality_review": PromptTemplate(
                name="code_quality_review",
                system_instructions="You are an expert software engineer. Review for code quality, readability, and adherence to best practices.",
                required_sections=["code_context"],
                output_format_spec="{format_instructions}"
            ),
            "repository_review": PromptTemplate(
                name="repository_review",
                system_instructions="You are a senior engineer. Provide a holistic review of the repository structure and cross-file dependencies.",
                required_sections=["repo_context"],
                output_format_spec="{format_instructions}"
            ),
            "mixed_review": PromptTemplate(
                name="mixed_review",
                system_instructions="You are a principal engineer. Perform a comprehensive review covering security, performance, quality, and architecture.",
                required_sections=["code_context"],
                output_format_spec="{format_instructions}"
            )
        }

    def get_template(self, template_name: str) -> PromptTemplate:
        """Retrieve a template by name."""
        if template_name not in self._templates:
            raise ValueError(f"Template '{template_name}' not found.")
        return self._templates[template_name]

    def render_template(self, template: PromptTemplate, context_blocks: Dict[str, str], output_format: str = "json") -> Tuple[str, str]:
        """Render a template with context blocks and output format."""
        
        # Render available context blocks
        system_prompt = template.system_instructions
        if output_format == "json":
            format_instructions = "Return the output as valid JSON."
        elif output_format == "markdown":
            format_instructions = "Return the output as Markdown."
        elif output_format == "typed_objects":
            format_instructions = "Return the output as typed objects according to the schema."
        else:
            format_instructions = f"Return the output in {output_format} format."
            
        system_prompt = template.system_instructions
        
        user_prompt = "Context:\n"
        for name, block in context_blocks.items():
            user_prompt += f"\n--- {name.upper()} ---\n{block}\n"
            
        user_prompt += f"\nOutput Format Instructions:\n{template.output_format_spec.format(format_instructions=format_instructions)}\n"
        
        return system_prompt, user_prompt
