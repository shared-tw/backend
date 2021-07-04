# Borrow from https://github.com/vitalik/django-ninja/issues/104#issuecomment-805939752

from typing import Any, Generic, List, Optional, TypeVar
from urllib import parse

import pydantic
from django.core.paginator import Page, Paginator
from django.utils.encoding import force_str
from pydantic.generics import GenericModel


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.

    Taken from: https://github.com/encode/django-rest-framework/blob/master/rest_framework/utils/urls.py
    """

    (scheme, netloc, path, query, fragment) = parse.urlsplit(force_str(url))
    query_dict = parse.parse_qs(query, keep_blank_values=True)
    query_dict[force_str(key)] = [force_str(val)]
    query = parse.urlencode(sorted(query_dict.items()), doseq=True)
    return parse.urlunsplit((scheme, netloc, path, query, fragment))


def get_next_page_url(request, page: Page) -> Optional[str]:
    if not page.has_next():
        return None
    return replace_query_param(request.build_absolute_uri(), "page", page.number + 1)


def get_previous_page_url(request, page: Page) -> Optional[str]:
    if not page.has_previous():
        return None
    return replace_query_param(request.build_absolute_uri(), "page", page.number - 1)


def render(request, *, schema_cls: Any, items: Any, page: int, page_size: int = 20):
    page = Paginator(items, per_page=page_size).get_page(page)
    items = [schema_cls.from_orm(item) for item in items]
    return PaginatedResponse[schema_cls](
        count=page.paginator.count,
        next=get_next_page_url(request, page),
        previous=get_previous_page_url(request, page),
        results=items,
    )


# Schemas
GenericResultsType = TypeVar("GenericResultsType")


class PaginatedResponse(GenericModel, Generic[GenericResultsType]):
    count: int
    next: Optional[pydantic.AnyHttpUrl]
    previous: Optional[pydantic.AnyHttpUrl]
    results: List[GenericResultsType]
