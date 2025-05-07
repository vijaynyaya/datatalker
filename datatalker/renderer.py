import dspy
from datatalker.types import Resource

class JSONToMarkdown(dspy.Signature):
    json_object = dspy.InputField(desc="JSON object to render")
    markdown = dspy.OutputField(desc="Markdown rendering")

class MarkdownRenderer(dspy.Module):
    def __init__(self, instructions: str, adapter = lambda x: x):
        """
        Sets up a renderer that can convert JSON data to Markdown format
        using specified instructions and an optional data adapter.
        Parameters
        ----------
        instructions : str
            The instructions used to guide the JSON to Markdown conversion process.
        adapter : callable, optional
            A function to pre-process the input data before rendering.
            Default is the identity function (lambda x: x).
        """
        self.adapter = adapter
        self.signature = JSONToMarkdown.with_instructions(instructions)
        self.renderer = dspy.ChainOfThought(self.signature)
    
    def forward(self, json):
        json = self.adapter(json)
        prediction = self.renderer(json_object=json)
        return prediction.markdown


def adapt_resource_for_rendering(doc: Resource):
    """Simplifies the resource doc for optimized markdown rendition."""
    return dict(
        title=doc["metadatas"]["title"],
        url=doc["metadatas"]["url"],
        long_text_description=doc['long_text'],
    )

ResourceRenderer = MarkdownRenderer(
    instructions=(
            "Render as a list item."
            "Start with the title as a formatted link."
            "Followed by a crispy short passage."
        ),
    adapter=adapt_resource_for_rendering
)