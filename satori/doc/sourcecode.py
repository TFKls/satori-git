"""Enhances docutils document structure with source code block support,
using pygments for highlighting.
"""


from docutils.nodes import Inline, FixedTextElement, literal_block
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import register_directive
from pygments.lexers import get_lexer_by_name


class code_token(Inline, FixedTextElement):              # pylint: disable-msg=C0103,R0904
    """A `Node` representing single source token."""

    pass


class code_block(literal_block):                         # pylint: disable-msg=C0103,R0904
    """A `Node` representing a (formatted) source code block."""

    pass


class Code(Directive):
    """A docutils `Directive` creating source code blocks."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}
    has_content = True
    node_class = code_block

    def run(self):
        """Execute this directive.
        """
        self.assert_has_content()
        lang = self.arguments[0]
        code = '\n'.join(self.content)
        lexer = get_lexer_by_name(lang)
        tokens = lexer.get_tokens(code)
        node = self.node_class()
        node['classes'] += ['code']
        for type_, text in tokens:
            node.append(code_token(text=text, type=type_))
            return [node]


register_directive('code', Code)
register_directive('sourcecode', Code)
