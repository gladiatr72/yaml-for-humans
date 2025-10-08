"""Tests for CliConfig dataclass and configuration management."""

import pytest
from dataclasses import FrozenInstanceError

from yaml_for_humans.cli import (
    CliConfig,
    OutputContext,
    ProcessingContext,
    DEFAULT_INDENT,
    DEFAULT_TIMEOUT_MS,
    DEFAULT_PRESERVE_EMPTY_LINES,
    DEFAULT_PRESERVE_COMMENTS,
)


class TestCliConfigDefaults:
    """Test CliConfig default values."""

    def test_cli_config_default_values(self):
        """CliConfig should use module defaults when no args provided."""
        config = CliConfig()

        assert config.indent == DEFAULT_INDENT
        assert config.timeout == DEFAULT_TIMEOUT_MS
        assert config.inputs is None
        assert config.output is None
        assert config.auto is False
        assert config.processing is not None

    def test_cli_config_default_processing_context(self):
        """CliConfig should create default ProcessingContext automatically."""
        config = CliConfig()

        assert isinstance(config.processing, ProcessingContext)
        assert config.processing.unsafe_inputs is False
        assert config.processing.preserve_empty_lines == DEFAULT_PRESERVE_EMPTY_LINES
        assert config.processing.preserve_comments == DEFAULT_PRESERVE_COMMENTS


class TestCliConfigCustomization:
    """Test CliConfig with custom values."""

    def test_cli_config_with_custom_values(self):
        """CliConfig should accept custom values for all fields."""
        config = CliConfig(
            indent=4,
            timeout=5000,
            inputs="file1.yaml,file2.yaml",
            output="/tmp/output/",
            auto=True,
        )

        assert config.indent == 4
        assert config.timeout == 5000
        assert config.inputs == "file1.yaml,file2.yaml"
        assert config.output == "/tmp/output/"
        assert config.auto is True

    def test_cli_config_with_custom_processing_context(self):
        """CliConfig should accept custom ProcessingContext."""
        processing = ProcessingContext(
            unsafe_inputs=True,
            preserve_empty_lines=False,
            preserve_comments=False,
        )
        config = CliConfig(processing=processing)

        assert config.processing.unsafe_inputs is True
        assert config.processing.preserve_empty_lines is False
        assert config.processing.preserve_comments is False


class TestCliConfigImmutability:
    """Test that CliConfig is immutable (frozen)."""

    def test_cli_config_is_frozen(self):
        """CliConfig should be immutable after creation."""
        config = CliConfig()

        with pytest.raises(FrozenInstanceError):
            config.indent = 10

    def test_cli_config_processing_context_is_frozen(self):
        """ProcessingContext within CliConfig should be immutable."""
        config = CliConfig()

        with pytest.raises(FrozenInstanceError):
            config.processing.unsafe_inputs = True


class TestCliConfigOutputContext:
    """Test output_context property derivation."""

    def test_output_context_derivation_defaults(self):
        """output_context should derive from CliConfig with defaults."""
        config = CliConfig()
        output_ctx = config.output_context

        assert isinstance(output_ctx, OutputContext)
        assert output_ctx.indent == DEFAULT_INDENT
        assert output_ctx.preserve_empty_lines == DEFAULT_PRESERVE_EMPTY_LINES
        assert output_ctx.preserve_comments == DEFAULT_PRESERVE_COMMENTS
        assert output_ctx.auto_create_dirs is False

    def test_output_context_derivation_custom_indent(self):
        """output_context should reflect custom indent from CliConfig."""
        config = CliConfig(indent=4)
        output_ctx = config.output_context

        assert output_ctx.indent == 4

    def test_output_context_derivation_custom_auto(self):
        """output_context should reflect auto flag from CliConfig."""
        config = CliConfig(auto=True)
        output_ctx = config.output_context

        assert output_ctx.auto_create_dirs is True

    def test_output_context_derivation_custom_preservation(self):
        """output_context should reflect preservation settings from ProcessingContext."""
        processing = ProcessingContext(
            preserve_empty_lines=False,
            preserve_comments=True,
        )
        config = CliConfig(processing=processing)
        output_ctx = config.output_context

        assert output_ctx.preserve_empty_lines is False
        assert output_ctx.preserve_comments is True

    def test_output_context_derivation_all_custom(self):
        """output_context should correctly derive from fully customized CliConfig."""
        processing = ProcessingContext(
            unsafe_inputs=True,
            preserve_empty_lines=False,
            preserve_comments=True,
        )
        config = CliConfig(
            indent=8,
            auto=True,
            processing=processing,
        )
        output_ctx = config.output_context

        assert output_ctx.indent == 8
        assert output_ctx.auto_create_dirs is True
        assert output_ctx.preserve_empty_lines is False
        assert output_ctx.preserve_comments is True


class TestCliConfigComposition:
    """Test CliConfig composition with ProcessingContext."""

    def test_cli_config_accesses_processing_properties(self):
        """CliConfig should provide access to ProcessingContext properties."""
        processing = ProcessingContext(unsafe_inputs=True)
        config = CliConfig(processing=processing)

        # Access through nested context
        assert config.processing.unsafe_inputs is True
        assert config.processing.is_safe_mode is False

    def test_cli_config_preserves_processing_context_methods(self):
        """CliConfig should preserve ProcessingContext computed properties."""
        processing = ProcessingContext(
            preserve_empty_lines=True,
            preserve_comments=True,
        )
        config = CliConfig(processing=processing)

        assert config.processing.is_preservation_enabled is True

    def test_cli_config_with_no_preservation(self):
        """CliConfig should work with preservation disabled."""
        processing = ProcessingContext(
            preserve_empty_lines=False,
            preserve_comments=False,
        )
        config = CliConfig(processing=processing)

        assert config.processing.is_preservation_enabled is False


class TestCliConfigFactoryPatterns:
    """Test common factory patterns for creating CliConfig."""

    def test_create_unsafe_config(self):
        """Helper pattern: create config with unsafe inputs."""
        processing = ProcessingContext(unsafe_inputs=True)
        config = CliConfig(processing=processing)

        assert config.processing.unsafe_inputs is True

    def test_create_file_output_config(self):
        """Helper pattern: create config for file output."""
        config = CliConfig(
            inputs="input.yaml",
            output="/tmp/output.yaml",
        )

        assert config.inputs == "input.yaml"
        assert config.output == "/tmp/output.yaml"

    def test_create_directory_output_config(self):
        """Helper pattern: create config for directory output with auto-create."""
        config = CliConfig(
            inputs="input.yaml",
            output="/tmp/output/",
            auto=True,
        )

        assert config.output == "/tmp/output/"
        assert config.auto is True

    def test_create_minimal_preservation_config(self):
        """Helper pattern: create config with no preservation features."""
        processing = ProcessingContext(
            preserve_empty_lines=False,
            preserve_comments=False,
        )
        config = CliConfig(
            indent=2,
            processing=processing,
        )

        assert config.processing.preserve_empty_lines is False
        assert config.processing.preserve_comments is False
        output_ctx = config.output_context
        assert output_ctx.preserve_empty_lines is False
        assert output_ctx.preserve_comments is False
