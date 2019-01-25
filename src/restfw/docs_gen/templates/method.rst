{{ method|rst_header('=') }}

{{ description }}

Status codes
------------

{{ status_codes }}

{% if input_schema or output_schema %}
Data schemas
------------

{% if input_schema %}
Input schema (``{{ input_schema.class_name }}``):

.. raw:: html

    <div class="json-schema"><code>
    {{ input_schema.serialized_schema|indent(4) }}
    </code></div>

{% endif %}
{% if output_schema %}
Output schema (``{{ output_schema.class_name }}``):

.. raw:: html

    <div class="json-schema"><code>
    {{ output_schema.serialized_schema|indent(4) }}
    </code></div>

{% endif %}

{% endif %}

Access list
-----------

{% for principal in allowed_principals %}
- {{ principal }}
{% endfor %}

Examples
--------

{% for example in examples %}
{{ example }}
{% if not loop.last %}

----
{% endif %}

{% endfor %}
