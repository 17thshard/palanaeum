from django import template
import re

register = template.Library()


class SpacelessNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return strip_spaces_between_tags(self.nodelist.render(context).strip())


@register.tag
def vuespaceless(parser, token):
    nodelist = parser.parse(('endvuespaceless',))
    parser.delete_first_token()
    return SpacelessNode(nodelist)


def strip_spaces_between_tags(value):
    value = re.sub(r'\n\s+', ' ', value)  # Replace all leading spaces at the beginning of a line!
    return re.sub(r'>\s+<(?!!)', '><', value)
