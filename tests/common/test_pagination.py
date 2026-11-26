# -*- coding: utf-8 -*-

# ======================================================================
# tests/common/test_pagination.py
#
# Tests del contrato de paginación (app/common/contracts/pagination.py).
# ======================================================================

from __future__ import annotations

from app.common.contracts import Page, PageRequest
from app.common.contracts.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class TestPageRequest:
    def test_offset_and_limit(self):
        request = PageRequest.of(3, 20)
        assert request.offset == 40
        assert request.limit == 20

    def test_first_page_has_no_offset(self):
        assert PageRequest.of(1, 50).offset == 0

    def test_clamps_invalid_values(self):
        request = PageRequest.of(0, 0)
        assert request.page == 1
        assert request.page_size == 1

    def test_caps_page_size(self):
        assert PageRequest.of(1, 10_000).page_size == MAX_PAGE_SIZE

    def test_defaults_when_missing(self):
        request = PageRequest.of(None, None)
        assert request.page == 1
        assert request.page_size == DEFAULT_PAGE_SIZE


class TestPage:
    def test_total_pages_rounds_up(self):
        assert Page(items=[], total=41, page=1, page_size=20).total_pages == 3

    def test_total_pages_exact(self):
        assert Page(items=[], total=40, page=1, page_size=20).total_pages == 2

    def test_total_pages_empty(self):
        assert Page(items=[], total=0, page=1, page_size=20).total_pages == 0

    def test_empty_keeps_request(self):
        page = Page.empty(PageRequest.of(4, 10))
        assert (page.items, page.total, page.page, page.page_size) == ([], 0, 4, 10)

    def test_map_transforms_items_and_keeps_meta(self):
        page = Page(items=[1, 2], total=12, page=2, page_size=2).map(lambda n: n * 10)
        assert page.items == [10, 20]
        assert (page.total, page.page, page.page_size) == (12, 2, 2)
