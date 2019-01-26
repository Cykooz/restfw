{{ title|rst_header('^') }}

**Request**:

  **{{ method }}** \{{ url }}

{% if headers %}
  Headers::

{% for key, value in headers.items() %}
    {{ key }}: {{ value }}
{% endfor %}
{% endif %}

{% if params %}
  Body:

  .. code-block:: js

    {{ params|indent(4) }}

{% endif %}

**Response**:

  Status: {{ response_status }}

{% if response_headers %}
  Headers::

{% for key, value in response_headers.items() %}
    {{ key }}: {{ value }}
{% endfor %}
{% endif %}

{% if response_status != 204 %}
  Body:

  .. code-block:: js

    {{ response_body|indent(4) }}

{% endif %}
