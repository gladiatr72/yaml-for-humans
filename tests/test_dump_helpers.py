"""
Tests for dump() helper functions.

Tests pure helper functions extracted from dump() complexity reduction.
"""

import pytest

from yaml_for_humans.dumper import (
    DumpConfig,
    _select_dumper,
    _build_dump_kwargs,
    _create_preset_dumper,
    _setup_formatting_dumper,
)
from yaml_for_humans.emitter import HumanFriendlyDumper
from yaml_for_humans.formatting_emitter import FormattingAwareDumper


class TestSelectDumper:
    """Test _select_dumper pure function."""

    def test_select_no_preservation(self):
        """Test selecting dumper when no preservation flags set."""
        dumper = _select_dumper(preserve_empty_lines=False, preserve_comments=False)
        assert dumper == HumanFriendlyDumper

    def test_select_with_empty_lines(self):
        """Test selecting dumper when preserve_empty_lines enabled."""
        dumper = _select_dumper(preserve_empty_lines=True, preserve_comments=False)
        assert dumper == FormattingAwareDumper

    def test_select_with_comments(self):
        """Test selecting dumper when preserve_comments enabled."""
        dumper = _select_dumper(preserve_empty_lines=False, preserve_comments=True)
        assert dumper == FormattingAwareDumper

    def test_select_with_both(self):
        """Test selecting dumper when both preservation flags enabled."""
        dumper = _select_dumper(preserve_empty_lines=True, preserve_comments=True)
        assert dumper == FormattingAwareDumper


class TestBuildDumpKwargs:
    """Test _build_dump_kwargs pure function."""

    def test_build_defaults_only(self):
        """Test building kwargs with only defaults."""
        kwargs = _build_dump_kwargs(HumanFriendlyDumper)
        assert kwargs["Dumper"] == HumanFriendlyDumper
        assert kwargs["default_flow_style"] is False
        assert kwargs["indent"] == 2
        assert kwargs["sort_keys"] is False
        assert kwargs["width"] == 120

    def test_build_with_user_overrides(self):
        """Test that user kwargs override defaults."""
        kwargs = _build_dump_kwargs(
            HumanFriendlyDumper,
            indent=4,
            width=80,
            custom_param="value"
        )
        assert kwargs["indent"] == 4  # Overridden
        assert kwargs["width"] == 80  # Overridden
        assert kwargs["custom_param"] == "value"  # Added
        assert kwargs["Dumper"] == HumanFriendlyDumper  # Default preserved

    def test_build_preserves_dumper_class(self):
        """Test that dumper class is preserved in kwargs."""
        kwargs = _build_dump_kwargs(FormattingAwareDumper)
        assert kwargs["Dumper"] == FormattingAwareDumper

    def test_build_with_empty_user_kwargs(self):
        """Test building with explicitly empty user kwargs."""
        kwargs = _build_dump_kwargs(HumanFriendlyDumper, **{})
        assert len(kwargs) == 5  # Only defaults

    def test_build_user_can_override_dumper(self):
        """Test that user can override Dumper in kwargs."""
        kwargs = _build_dump_kwargs(
            HumanFriendlyDumper,
            Dumper=FormattingAwareDumper
        )
        assert kwargs["Dumper"] == FormattingAwareDumper


class TestCreatePresetDumper:
    """Test _create_preset_dumper pure function."""

    def test_create_with_empty_lines(self):
        """Test creating preset dumper with empty lines preservation."""
        PresetDumper = _create_preset_dumper(
            FormattingAwareDumper,
            preserve_empty_lines=True,
            preserve_comments=False
        )
        # Verify it's a class
        assert isinstance(PresetDumper, type)
        # Verify it inherits from base
        assert issubclass(PresetDumper, FormattingAwareDumper)

    def test_create_with_comments(self):
        """Test creating preset dumper with comments preservation."""
        PresetDumper = _create_preset_dumper(
            FormattingAwareDumper,
            preserve_empty_lines=False,
            preserve_comments=True
        )
        assert isinstance(PresetDumper, type)
        assert issubclass(PresetDumper, FormattingAwareDumper)

    def test_create_with_both_flags(self):
        """Test creating preset dumper with both preservation flags."""
        PresetDumper = _create_preset_dumper(
            FormattingAwareDumper,
            preserve_empty_lines=True,
            preserve_comments=True
        )
        assert isinstance(PresetDumper, type)
        assert issubclass(PresetDumper, FormattingAwareDumper)

    def test_create_with_no_flags(self):
        """Test creating preset dumper with no preservation flags."""
        PresetDumper = _create_preset_dumper(
            FormattingAwareDumper,
            preserve_empty_lines=False,
            preserve_comments=False
        )
        assert isinstance(PresetDumper, type)
        assert issubclass(PresetDumper, FormattingAwareDumper)

    def test_created_dumper_is_unique(self):
        """Test that each call creates a new unique class."""
        Dumper1 = _create_preset_dumper(
            FormattingAwareDumper, True, False
        )
        Dumper2 = _create_preset_dumper(
            FormattingAwareDumper, True, False
        )
        # Should be different classes even with same params
        assert Dumper1 is not Dumper2


class TestDumpConfig:
    """Test DumpConfig dataclass and properties."""

    def test_needs_formatting_both_false(self):
        """Test needs_formatting returns False when no preservation enabled."""
        config = DumpConfig(
            preserve_empty_lines=False,
            preserve_comments=False
        )
        assert config.needs_formatting is False

    def test_needs_formatting_empty_lines_only(self):
        """Test needs_formatting returns True when preserve_empty_lines enabled."""
        config = DumpConfig(
            preserve_empty_lines=True,
            preserve_comments=False
        )
        assert config.needs_formatting is True

    def test_needs_formatting_comments_only(self):
        """Test needs_formatting returns True when preserve_comments enabled."""
        config = DumpConfig(
            preserve_empty_lines=False,
            preserve_comments=True
        )
        assert config.needs_formatting is True

    def test_needs_formatting_both_true(self):
        """Test needs_formatting returns True when both flags enabled."""
        config = DumpConfig(
            preserve_empty_lines=True,
            preserve_comments=True
        )
        assert config.needs_formatting is True

    def test_config_is_frozen(self):
        """Test that DumpConfig is immutable (frozen dataclass)."""
        config = DumpConfig(preserve_empty_lines=True)
        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            config.preserve_empty_lines = False


class TestSetupFormattingDumper:
    """Test _setup_formatting_dumper pure function."""

    def test_setup_removes_preservation_params(self):
        """Test that preservation parameters are removed from kwargs."""
        config = DumpConfig(preserve_empty_lines=True, preserve_comments=True)
        kwargs = {
            "Dumper": FormattingAwareDumper,
            "indent": 2,
            "preserve_empty_lines": True,  # Should be removed
            "preserve_comments": True,  # Should be removed
        }
        result = _setup_formatting_dumper(config, kwargs)

        assert "preserve_empty_lines" not in result
        assert "preserve_comments" not in result
        assert result["indent"] == 2

    def test_setup_creates_preset_dumper(self):
        """Test that preset dumper is created when Dumper is FormattingAwareDumper."""
        config = DumpConfig(preserve_empty_lines=True, preserve_comments=False)
        kwargs = {"Dumper": FormattingAwareDumper, "indent": 2}
        result = _setup_formatting_dumper(config, kwargs)

        # Dumper should be replaced with preset
        assert result["Dumper"] != FormattingAwareDumper
        assert issubclass(result["Dumper"], FormattingAwareDumper)

    def test_setup_preserves_other_kwargs(self):
        """Test that other kwargs are preserved unchanged."""
        config = DumpConfig(preserve_empty_lines=True)
        kwargs = {
            "Dumper": FormattingAwareDumper,
            "indent": 4,
            "width": 80,
            "sort_keys": True,
        }
        result = _setup_formatting_dumper(config, kwargs)

        assert result["indent"] == 4
        assert result["width"] == 80
        assert result["sort_keys"] is True

    def test_setup_does_not_mutate_input(self):
        """Test that input kwargs dict is not mutated."""
        config = DumpConfig(preserve_empty_lines=True)
        kwargs = {
            "Dumper": FormattingAwareDumper,
            "indent": 2,
            "preserve_empty_lines": True,
        }
        original_dumper = kwargs["Dumper"]
        original_keys = set(kwargs.keys())

        _setup_formatting_dumper(config, kwargs)

        # Original should be unchanged
        assert kwargs["Dumper"] == original_dumper
        assert set(kwargs.keys()) == original_keys
        assert kwargs["preserve_empty_lines"] is True

    def test_setup_with_non_formatting_dumper(self):
        """Test setup when Dumper is not FormattingAwareDumper."""
        config = DumpConfig(preserve_empty_lines=True)
        kwargs = {"Dumper": HumanFriendlyDumper, "indent": 2}
        result = _setup_formatting_dumper(config, kwargs)

        # Should not create preset for non-formatting dumper
        assert result["Dumper"] == HumanFriendlyDumper


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
