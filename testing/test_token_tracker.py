"""Unit tests for Token Tracker."""

import pytest
import json
import os
import tempfile
import time
from token_tracker import TokenTracker, TokenCosts, TokenRecord, get_token_tracker


class TestTokenCosts:
    """Test suite for TokenCosts dataclass."""

    def test_token_costs_creation(self):
        """Test TokenCosts dataclass creation."""
        costs = TokenCosts(
            model_name="gpt-4", input_cost_per_1k=0.03, output_cost_per_1k=0.06
        )

        assert costs.model_name == "gpt-4"
        assert costs.input_cost_per_1k == 0.03
        assert costs.output_cost_per_1k == 0.06
        assert costs.currency == "USD"


class TestTokenRecord:
    """Test suite for TokenRecord dataclass."""

    def test_token_record_creation(self):
        """Test TokenRecord dataclass creation."""
        record = TokenRecord(
            timestamp=time.time(),
            agent_name="coder",
            model_name="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.045,
        )

        assert record.agent_name == "coder"
        assert record.model_name == "gpt-4"
        assert record.input_tokens == 100
        assert record.output_tokens == 50
        assert record.total_tokens == 150
        assert record.estimated_cost == 0.045

    def test_token_record_to_dict(self):
        """Test converting TokenRecord to dictionary."""

        record = TokenRecord(
            timestamp=time.time(),
            agent_name="planner",
            model_name="gpt-4",
            input_tokens=50,
            output_tokens=25,
            total_tokens=75,
            estimated_cost=0.0225,
        )

        record_dict = record.to_dict()

        assert isinstance(record_dict, dict)
        assert "agent_name" in record_dict
        assert "model_name" in record_dict
        assert "total_tokens" in record_dict
        assert "estimated_cost" in record_dict


class TestTokenTracker:
    """Test suite for TokenTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh tracker for each test using temp file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name
        yield TokenTracker(storage_path=temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_initialization_default_costs(self, tracker):
        """Test tracker initializes with default model costs."""
        assert "gpt-4" in tracker._model_costs
        assert "gpt-4-turbo" in tracker._model_costs
        assert "gpt-4o" in tracker._model_costs
        assert "gpt-3.5-turbo" in tracker._model_costs
        assert "gpt-oss:120b-cloud" in tracker._model_costs

    def test_initialization_with_limits(self):
        """Test tracker initializes with limits."""
        tracker = TokenTracker(daily_token_limit=10000, daily_cost_limit=5.0)

        assert tracker._daily_token_limit == 10000
        assert tracker._daily_cost_limit == 5.0

    def test_calculate_cost_gpt4(self, tracker):
        """Test cost calculation for GPT-4."""
        cost = tracker._calculate_cost("gpt-4", 1000, 1000)

        expected = (1000 / 1000) * 0.03 + (1000 / 1000) * 0.06
        assert cost == pytest.approx(expected)

    def test_calculate_cost_unknown_model(self, tracker):
        """Test cost calculation for unknown model returns 0."""
        cost = tracker._calculate_cost("unknown-model", 100, 50)

        assert cost == 0.0

    def test_update_session_stats(self, tracker):
        """Test updating session statistics."""
        tracker._update_session_stats("gpt-4", 150, 0.045)

        assert tracker._current_session_tokens["gpt-4"] == 150
        assert tracker._current_session_costs["gpt-4"] == 0.045

    def test_get_session_summary(self, tracker):
        """Test getting session summary."""
        tracker._update_session_stats("gpt-4", 100, 0.03)
        tracker._update_session_stats("gpt-4o-mini", 50, 0.0015)

        summary = tracker.get_session_summary()

        assert summary["total_tokens"] == 150
        assert summary["total_cost"] == pytest.approx(0.0315, abs=0.0001)
        assert "gpt-4" in summary["by_model"]
        assert "gpt-4o-mini" in summary["by_model"]

    def test_get_daily_tokens(self, tracker):
        """Test getting daily token usage."""
        from datetime import datetime

        now = datetime.now()

        record = TokenRecord(
            timestamp=now.timestamp(),
            agent_name="coder",
            model_name="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost=0.045,
        )
        tracker._records.append(record)

        daily = tracker.get_daily_tokens()

        assert daily["total"] == 150
        assert daily["input"] == 100
        assert daily["output"] == 50

    def test_get_daily_cost(self, tracker):
        """Test getting daily cost."""
        from datetime import datetime

        now = datetime.now()

        tracker._records.append(
            TokenRecord(
                timestamp=now.timestamp(),
                agent_name="coder",
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.045,
            )
        )

        cost = tracker.get_daily_cost()

        assert cost == pytest.approx(0.045, abs=0.001)

    def test_get_usage_by_agent(self, tracker):
        """Test getting usage by agent."""
        tracker._records.append(
            TokenRecord(
                timestamp=time.time(),
                agent_name="coder",
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.045,
            )
        )
        tracker._records.append(
            TokenRecord(
                timestamp=time.time(),
                agent_name="coder",
                model_name="gpt-4",
                input_tokens=50,
                output_tokens=25,
                total_tokens=75,
                estimated_cost=0.0225,
            )
        )

        usage = tracker.get_usage_by_agent("coder")

        assert usage["agent"] == "coder"
        assert usage["total_calls"] == 2
        assert usage["total_tokens"] == 225
        assert "by_model" in usage

    def test_get_usage_history(self, tracker):
        """Test getting usage history."""
        now = time.time()

        for i in range(10):
            tracker._records.append(
                TokenRecord(
                    timestamp=now + i,
                    agent_name=f"agent{i}",
                    model_name="gpt-4",
                    input_tokens=10,
                    output_tokens=5,
                    total_tokens=15,
                    estimated_cost=0.0045,
                )
            )

        history = tracker.get_usage_history(hours=24)

        assert len(history) == 10

    def test_export_to_json(self, tracker):
        """Test exporting to JSON."""
        tracker._records.append(
            TokenRecord(
                timestamp=time.time(),
                agent_name="coder",
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.045,
            )
        )

        filepath = tracker.export_to_json()

        assert os.path.exists(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 1

        os.remove(filepath)

    def test_export_to_json_custom_path(self, tracker):
        """Test exporting to custom path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            temp_path = f.name

        tracker._records.append(
            TokenRecord(
                timestamp=time.time(),
                agent_name="coder",
                model_name="gpt-4",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                estimated_cost=0.045,
            )
        )

        filepath = tracker.export_to_json(temp_path)

        assert filepath == temp_path

        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_reset_session(self, tracker):
        """Test resetting session statistics."""
        tracker._update_session_stats("gpt-4", 100, 0.03)
        tracker._update_session_stats("gpt-4o-mini", 50, 0.0015)

        tracker.reset_session()

        assert len(tracker._current_session_tokens) == 0
        assert len(tracker._current_session_costs) == 0

    def test_set_model_cost(self, tracker):
        """Test setting model cost."""
        tracker.set_model_cost("custom-model", 0.01, 0.02)

        assert "custom-model" in tracker._model_costs
        assert tracker._model_costs["custom-model"].input_cost_per_1k == 0.01
        assert tracker._model_costs["custom-model"].output_cost_per_1k == 0.02

    def test_register_usage_callback(self, tracker):
        """Test registering usage callback."""
        callback_called = []

        def callback(record):
            callback_called.append(record)

        tracker.register_usage_callback(callback)

        assert len(tracker._on_usage_callbacks) == 1

    def test_register_limit_callback(self, tracker):
        """Test registering limit callback."""
        callback_called = []

        def callback(limit_type, model_name, value):
            callback_called.append((limit_type, model_name, value))

        tracker.register_limit_callback(callback)

        assert len(tracker._on_limit_callbacks) == 1


class TestGetTokenTracker:
    """Test suite for get_token_tracker singleton."""

    def test_get_tracker_creates_instance(self):
        """Test get_token_tracker creates new instance."""
        from token_tracker import _tracker

        _tracker = None
        tracker = get_token_tracker()

        assert tracker is not None
        assert isinstance(tracker, TokenTracker)

    def test_get_tracker_returns_singleton(self):
        """Test get_token_tracker returns same instance."""
        tracker1 = get_token_tracker()
        tracker2 = get_token_tracker()

        assert tracker1 is tracker2
