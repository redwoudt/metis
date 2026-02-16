from typing import Any
from .base import ToolCommand, ToolContext


class GenerateImageCommand(ToolCommand):
    name = "generate_image"

    def execute(self, context: ToolContext) -> Any:
        prompt = context.args.get("prompt")
        if not prompt:
            raise ValueError("Missing 'prompt' argument for image generation.")

        # Replace with your actual image generation logic
        return {"image_url": f"https://fake.images/{prompt.replace(' ', '_')}.png"}