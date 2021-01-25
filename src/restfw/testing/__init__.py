"""
:Authors: cykooz
:Date: 06.12.2016
"""
try:
    import pytest
    pytest.register_assert_rewrite(
        'restfw.testing.resource_testing',
        'restfw.testing.webapp',
    )
except (ImportError, AttributeError):
    pass

from .resource_testing import assert_resource
