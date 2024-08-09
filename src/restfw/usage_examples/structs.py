"""
:Authors: cykooz
:Date: 23.01.2019

Data structures to store information about resources, entry points
and usage examples collected by `UsageExamplesCollector`.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..typing import Json


@dataclass()
class UrlElement:
    value: str
    resource_class_name: str
    ep_id: Optional[str] = None


@dataclass()
class ResourceInfo:
    class_name: str
    description: List[str] = field(default_factory=list)
    count_of_entry_points: int = field(default=0, init=False)


@dataclass()
class SchemaInfo:
    class_name: str
    serialized_schema: Any
    description: List[str] = field(default_factory=list)


@dataclass()
class RequestInfo:
    url: str
    headers: Optional[dict] = None
    params: Optional[dict] = None


@dataclass()
class ResponseInfo:
    status_code: int
    status_name: str
    headers: Optional[dict] = None
    expected_headers: Optional[dict] = None
    json_body: Json = None


@dataclass()
class ExampleInfo:
    request_info: RequestInfo
    response_info: ResponseInfo
    description: Optional[str] = None
    exclude_from_doc: bool = False


@dataclass()
class Examples:
    examples_info: List[ExampleInfo]
    all_statuses: List[int] = field(init=False)

    def __post_init__(self):
        self.all_statuses = sorted(
            set(e.response_info.status_code for e in self.examples_info)
        )


@dataclass()
class MethodInfo:
    examples_info: List[ExampleInfo]
    input_schema: Optional[SchemaInfo] = None
    output_schema: Optional[SchemaInfo] = None
    allowed_principals: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)


@dataclass()
class EntryPointInfo:
    name: str
    examples_class_name: str
    resource_class_name: str
    url_elements: List[UrlElement]
    methods: Dict[str, MethodInfo]
    description: List[str] = field(default_factory=list)
