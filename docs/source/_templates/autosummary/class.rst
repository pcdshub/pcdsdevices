{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. device:: {{ module }}.{{ objname }}
    :inherited: ignore
    :title: :class:`{{objname}}`-defined ophyd components

.. device:: {{ module }}.{{ objname }}
    :inherited: only
    :title: :class:`{{objname}}` inherited ophyd components

.. autoclass:: {{ objname }}

   {% block methods %}
   .. automethod:: __init__

   {% if methods %}
   .. rubric:: Methods

   .. autosummary::
      :toctree: generated
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: Attributes

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}
