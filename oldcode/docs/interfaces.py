# -*- coding: utf-8 -*-
"""
:Authors: cykooz
:Date: 27.04.2015
"""
from __future__ import unicode_literals
from zope.interface import Interface, Attribute


class IUrlPlaceHolder(Interface):

    url_placeholder = Attribute('Placeholder for resource URL in the documentation')


class IResourceDocPrepare(Interface):

    resource_class = Attribute('Class of resource')

    def prepare_db(root, registry):
        """Prepare data base, create resource."""

    def get_example_request(method, resource):
        """Returns dictionary with example data for given request method"""

    def get_resource_info_from_db(root, registry):
        """Scan data base and return instance of ResourceInfo
        :rtype: .info.ResourceInfo
        """
