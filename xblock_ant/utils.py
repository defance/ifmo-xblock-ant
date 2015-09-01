import pkg_resources

from django.template import Context, Template


def render_template(template_path, context=None, package_name=__name__):
    """
    Evaluate a template by resource path, applying the provided context
    """
    if context is None:
        context = {}
    template_str = load_resource(template_path, package_name=package_name)
    template = Template(template_str)
    return template.render(Context(context))


def load_resource(resource_path, package_name=__name__):
    """
    Gets the content of a resource
    """
    resource_content = pkg_resources.resource_string(package_name, resource_path)
    return resource_content
    # return unicode(resource_content)


def resource_string(path, package_name=__name__):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(package_name, path)
    return data
    # return data.decode("utf8")