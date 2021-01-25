"""
:Authors: cykooz
:Date: 12.01.2021
"""
from functools import update_wrapper


def derive_fabric(fabric, predicates):
    def fabric_wrapper(resource):
        if all((predicate(resource) for predicate in predicates)):
            return fabric(resource)

    if hasattr(fabric, '__name__'):
        update_wrapper(fabric_wrapper, fabric)

    return fabric_wrapper
