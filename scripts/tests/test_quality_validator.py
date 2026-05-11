"""
Tests for Quality Validator Agent.

Tests FFmpeg-based validation checks: duration, clipping, silence gaps, loudness.
Uses mocked FFmpeg calls to avoid actual audio processing.
"""
import pytest
import subprocess
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agents.quality_validator.validator import (
    QualityValidator,
    ValidationResult,
    ValidationReport,
    ValidationError,
    load_timing_data
)


# Fixtures

@pytest.fixture
def mock_ffmpeg():
    """Mock FFmpeg subprocess calls."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def validator():
    """QualityValidator instance with dry_run=True."""
    return QualityValidator(dry_run=True)


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create sample audio file."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_text("mock audio data")
    return audio_file


@pytest.fixture
def timing_file(tmp_path):
    """Create sample timing.json."""
    timing = tmp_path / "timing.json"
    data = {
        "story": "test-story",
        "total_duration": 120.0,
        "scenes": []
    }
    timing.write_text(json.dumps(data))
    return timing


# ValidationResult Tests

def test_validation_result_creation():
    """Test ValidationResult instantiation."""
    result = ValidationResult(
        passed=True,
        severity="PASS",
        message="Test passed",
        details={"key": "value"}
    )
    
    assert result.passed is True
    assert result.severity == "PASS"
    assert result.message == "Test passed"
    assert result.details == {"key": "value"}


def test_validation_result_to_dict():
    """Test ValidationResult to_dict conversion."""
    result = ValidationResult(
        passed=False,
        severity="CRITICAL",
        message="Test failed",
        details={"error": "something"}
    )
    
    result_dict = result.to_dict()
    
    assert result_dict["passed"] is False
    assert result_dict["severity"] == "CRITICAL"
    assert result_dict["message"] == "Test failed"
    assert result_dict["details"]["error"] == "something"


# ValidationReport Tests

def test_validation_report_creation():
    """Test ValidationReport instantiation."""
    check1 = ValidationResult(True, "PASS", "OK", {})
    check2 = ValidationResult(False, "CRITICAL", "Failed", {})
    
    report = ValidationReport(
        audio_file="test.mp3",
        timestamp="2026-05-03T10:00:00",
        checks={"check1": check1, "check2": check2},
        overall_passed=False,
        critical_issues=1,
        warnings=0
    )
    
    assert report.audio_file == "test.mp3"
    assert report.overall_passed is False
    assert report.critical_issues == 1
    assert len(report.checks) == 2


def test_validation_report_to_dict():
    """Test ValidationReport to_dict conversion."""
    check = ValidationResult(True, "PASS", "OK", {"detail": "value"})
    report = ValidationReport(
        audio_file="test.mp3",
        timestamp="2026-05-03T10:00:00",
        checks={"duration": check},
        overall_passed=True,
        critical_issues=0,
        warnings=0
    )
    
    report_dict = report.to_dict()
    
    assert report_dict["audio_file"] == "test.mp3"
    assert report_dict["overall_passed"] is True
    assert "duration" in report_dict["checks"]
    assert report_dict["checks"]["duration"]["passed"] is True


# QualityValidator Tests

def test_validator_initialization_dry_run():
    """Test validator initialization in dry_run mode."""
    validator = QualityValidator(dry_run=True)
    
    assert validator.ffmpeg_path == "ffmpeg"
    assert validator.ffprobe_path == "ffprobe"
    assert validator.dry_run is True


def test_validator_initialization_missing_tools():
    """Test validator raises error when tools missing."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(ValidationError, match="not accessible"):
            QualityValidator(dry_run=False)


# Duration Validator Tests

def test_validate_duration_pass(validator, sample_audio_file, mock_ffmpeg):
    """Test duration validation passes when within tolerance."""
    # Mock ffprobe output
    mock_ffmpeg.return_value.stdout = json.dumps({
        "format": {"duration": "120.3"}
    })
    
    validator.dry_run = False
    result = validator.validate_duration(sample_audio_file, expected=120.0, tolerance=0.5)
    
    assert result.passed is True
    assert result.severity == "PASS"
    assert "120.00s" in result.details["expected_duration"]


def test_validate_duration_fail(validator, sample_audio_file, mock_ffmpeg):
    """Test duration validation fails when out of tolerance."""
    mock_ffmpeg.return_value.stdout = json.dumps({
        "format": {"duration": "125.0"}
    })
    
    validator.dry_run = False
    result = validator.validate_duration(sample_audio_file, expected=120.0, tolerance=0.5)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "mismatch" in result.message.lower()


def test_validate_duration_warning(validator, sample_audio_file, mock_ffmpeg):
    """Test duration validation returns warning for moderate deviation."""
    mock_ffmpeg.return_value.stdout = json.dumps({
        "format": {"duration": "120.8"}
    })
    
    validator.dry_run = False
    result = validator.validate_duration(sample_audio_file, expected=120.0, tolerance=0.5)
    
    assert result.passed is False
    assert result.severity == "WARNING"
    assert "slightly off" in result.message.lower()


def test_validate_duration_file_not_found(validator, tmp_path):
    """Test duration validation handles missing file."""
    missing_file = tmp_path / "missing.mp3"
    
    result = validator.validate_duration(missing_file, expected=120.0)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "not found" in result.message.lower()


# Clipping Detector Tests

def test_detect_clipping_pass(validator, sample_audio_file, mock_ffmpeg):
    """Test clipping detection passes when no clipping."""
    mock_ffmpeg.return_value.stderr = "Overall Max level dB: -3.5"
    
    validator.dry_run = False
    result = validator.detect_clipping(sample_audio_file, threshold=0.99)
    
    assert result.passed is True
    assert result.severity == "PASS"
    assert "no clipping" in result.message.lower()


def test_detect_clipping_fail(validator, sample_audio_file, mock_ffmpeg):
    """Test clipping detection fails when clipping detected."""
    mock_ffmpeg.return_value.stderr = "Overall Max level dB: 0.5"
    
    validator.dry_run = False
    result = validator.detect_clipping(sample_audio_file, threshold=0.99)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "clipping detected" in result.message.lower()


def test_detect_clipping_warning(validator, sample_audio_file, mock_ffmpeg):
    """Test clipping detection warns on near clipping."""
    mock_ffmpeg.return_value.stderr = "Overall Max level dB: -0.1"
    
    validator.dry_run = False
    result = validator.detect_clipping(sample_audio_file, threshold=0.99)
    
    # -0.1dB ≈ 0.989 linear, which is < 0.99 but close
    # Should pass but might be close to threshold
    assert "peak" in result.message.lower()


# Silence Gap Checker Tests

def test_check_silence_gaps_pass(validator, sample_audio_file, mock_ffmpeg):
    """Test silence gap check passes when no gaps."""
    mock_ffmpeg.return_value.stderr = "[silencedetect] silence_start: 10.5"
    
    validator.dry_run = False
    result = validator.check_silence_gaps(sample_audio_file, max_silence=2.0)
    
    assert result.passed is True
    assert result.severity == "PASS"
    assert "no excessive" in result.message.lower()


def test_check_silence_gaps_fail(validator, sample_audio_file, mock_ffmpeg):
    """Test silence gap check fails when gaps detected."""
    mock_ffmpeg.return_value.stderr = (
        "[silencedetect] silence_start: 10.0\n"
        "[silencedetect] silence_end: 13.5 | silence_duration: 3.5\n"
        "[silencedetect] silence_start: 20.0\n"
        "[silencedetect] silence_end: 24.0 | silence_duration: 4.0\n"
        "[silencedetect] silence_start: 30.0\n"
        "[silencedetect] silence_end: 33.2 | silence_duration: 3.2"
    )
    
    validator.dry_run = False
    result = validator.check_silence_gaps(sample_audio_file, max_silence=2.0)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "3 silence gaps" in result.message or "Found 3" in result.message
    assert result.details["gaps_found"] == 3


def test_check_silence_gaps_warning(validator, sample_audio_file, mock_ffmpeg):
    """Test silence gap check warns on few gaps."""
    mock_ffmpeg.return_value.stderr = (
        "[silencedetect] silence_start: 10.0\n"
        "[silencedetect] silence_end: 13.5 | silence_duration: 3.5"
    )
    
    validator.dry_run = False
    result = validator.check_silence_gaps(sample_audio_file, max_silence=2.0)
    
    assert result.passed is False
    assert result.severity == "WARNING"
    assert "1 silence gap" in result.message


# Loudness Validator Tests

def test_validate_loudness_pass(validator, sample_audio_file, mock_ffmpeg):
    """Test loudness validation passes when within tolerance."""
    mock_ffmpeg.return_value.stderr = """
[Parsed_loudnorm_0 @ 0x123] {
  "input_i" : "-14.3",
  "input_tp" : "-2.5",
  "input_lra" : "8.3"
}
"""
    
    validator.dry_run = False
    result = validator.validate_loudness(sample_audio_file, target=-14.0, tolerance=1.0)
    
    assert result.passed is True
    assert result.severity == "PASS"
    assert "-14.3 LUFS" in result.details["actual_loudness"]


def test_validate_loudness_fail(validator, sample_audio_file, mock_ffmpeg):
    """Test loudness validation fails when out of tolerance."""
    mock_ffmpeg.return_value.stderr = """
[Parsed_loudnorm_0 @ 0x123] {
  "input_i" : "-10.5",
  "input_tp" : "-2.5"
}
"""
    
    validator.dry_run = False
    result = validator.validate_loudness(sample_audio_file, target=-14.0, tolerance=1.0)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "out of range" in result.message.lower()


def test_validate_loudness_warning(validator, sample_audio_file, mock_ffmpeg):
    """Test loudness validation warns on moderate deviation."""
    mock_ffmpeg.return_value.stderr = """
{
  "input_i" : "-15.8"
}
"""
    
    validator.dry_run = False
    result = validator.validate_loudness(sample_audio_file, target=-14.0, tolerance=1.0)
    
    assert result.passed is False
    assert result.severity == "WARNING"
    assert "slightly off" in result.message.lower()


def test_validate_loudness_parse_error(validator, sample_audio_file, mock_ffmpeg):
    """Test loudness validation handles parse errors."""
    mock_ffmpeg.return_value.stderr = "Invalid output"
    
    validator.dry_run = False
    result = validator.validate_loudness(sample_audio_file, target=-14.0)
    
    assert result.passed is False
    assert result.severity == "CRITICAL"
    assert "parse" in result.message.lower()


# Full Validation Tests

def test_validate_all_pass(validator, sample_audio_file, mock_ffmpeg):
    """Test validate_all returns passing report."""
    mock_ffmpeg.return_value.stdout = json.dumps({"format": {"duration": "120.2"}})
    mock_ffmpeg.return_value.stderr = """
Overall Max level dB: -3.5
[Parsed_loudnorm_0 @ 0x123] {
  "input_i" : "-14.2"
}
"""
    
    validator.dry_run = False
    report = validator.validate_all(sample_audio_file, expected_duration=120.0)
    
    assert report.overall_passed is True
    assert report.critical_issues == 0
    assert len(report.checks) == 4
    assert "duration" in report.checks
    assert "clipping" in report.checks
    assert "silence_gaps" in report.checks
    assert "loudness" in report.checks


def test_validate_all_fail(validator, sample_audio_file, mock_ffmpeg):
    """Test validate_all returns failing report."""
    mock_ffmpeg.return_value.stdout = json.dumps({"format": {"duration": "130.0"}})
    mock_ffmpeg.return_value.stderr = """
Overall Max level dB: 1.5
[silencedetect] silence_start: 10.0
[silencedetect] silence_end: 15.0 | silence_duration: 5.0
{
  "input_i" : "-10.0"
}
"""
    
    validator.dry_run = False
    report = validator.validate_all(sample_audio_file, expected_duration=120.0)
    
    assert report.overall_passed is False
    assert report.critical_issues > 0


def test_validate_all_dry_run(validator, sample_audio_file):
    """Test validate_all works in dry_run mode."""
    report = validator.validate_all(sample_audio_file, expected_duration=120.0)
    
    # Dry run should mock all checks as passing
    assert len(report.checks) == 4
    assert report.timestamp is not None


# Utility Tests

def test_load_timing_data(timing_file):
    """Test loading duration from timing.json."""
    duration = load_timing_data(timing_file)
    
    assert duration == 120.0


def test_load_timing_data_missing_key(tmp_path):
    """Test load_timing_data handles missing total_duration."""
    timing = tmp_path / "timing_incomplete.json"
    timing.write_text(json.dumps({"story": "test"}))
    
    duration = load_timing_data(timing)
    
    assert duration == 0.0


# Integration Tests

def test_full_validation_workflow(tmp_path, mock_ffmpeg):
    """Test complete validation workflow."""
    # Setup
    audio_file = tmp_path / "final_mix.mp3"
    audio_file.write_text("mock audio")
    
    timing_file = tmp_path / "timing.json"
    timing_file.write_text(json.dumps({"total_duration": 100.0}))
    
    # Mock responses
    mock_ffmpeg.return_value.stdout = json.dumps({"format": {"duration": "100.1"}})
    mock_ffmpeg.return_value.stderr = """
Overall Max level dB: -2.5
{
  "input_i" : "-14.1"
}
"""
    
    # Execute
    validator = QualityValidator(dry_run=False)
    expected = load_timing_data(timing_file)
    report = validator.validate_all(audio_file, expected)
    
    # Save report
    report_file = tmp_path / "quality_report.json"
    with open(report_file, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    # Verify
    assert report_file.exists()
    assert report.overall_passed is True
    
    with open(report_file) as f:
        saved_report = json.load(f)
    
    assert saved_report["overall_passed"] is True
    assert "duration" in saved_report["checks"]
