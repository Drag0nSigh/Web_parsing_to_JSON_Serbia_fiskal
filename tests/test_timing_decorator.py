"""Тесты для utils/timing_decorator.py."""

import asyncio
from unittest.mock import patch

import pytest

from utils.timing_decorator import async_timing_decorator, timing_decorator


class TestTimingDecorator:
    def test_sync_success_fast(self):
        @timing_decorator
        def fn():
            return "ok"

        assert fn() == "ok"

    @patch("utils.timing_decorator.time")
    def test_sync_success_slow_branch(self, mock_time):
        mock_time.time.side_effect = [0.0, 1.5]

        @timing_decorator
        def fn():
            return 1

        assert fn() == 1

    @patch("utils.timing_decorator.time")
    def test_sync_raises_logs_error(self, mock_time):
        mock_time.time.side_effect = [0.0, 0.01]

        @timing_decorator
        def fn():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError, match="fail"):
            fn()


class TestAsyncTimingDecorator:
    @pytest.mark.asyncio
    async def test_async_success(self):
        @async_timing_decorator
        async def fn():
            return "async_ok"

        assert await fn() == "async_ok"

    @pytest.mark.asyncio
    @patch("utils.timing_decorator.time")
    async def test_async_success_slow_branch(self, mock_time):
        mock_time.time.side_effect = [0.0, 2.0]

        @async_timing_decorator
        async def fn():
            return 2

        assert await fn() == 2

    @pytest.mark.asyncio
    @patch("utils.timing_decorator.time")
    async def test_async_raises_logs_error(self, mock_time):
        mock_time.time.side_effect = [0.0, 0.02]

        @async_timing_decorator
        async def fn():
            raise ValueError("async fail")

        with pytest.raises(ValueError, match="async fail"):
            await fn()
