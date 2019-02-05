{{ name|rst_header('*') }}

Resource class:
    {{ resource_class_name }}

Resource path:
    {{ entry_point_url }}

Available methods:
    {{ available_methods }}

{{ resource_description }}

{% for method in methods %}
{{ method }}

{% endfor %}
