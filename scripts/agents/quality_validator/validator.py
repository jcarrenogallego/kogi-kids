"""
Quality Validator Agent - Audio Quality Checks.

Automated validation suite for generated audio:
1. Duration Validator - Verifies final mix matches expected timing
2. Clipping Detector - Checks for audio clipping/distortion
3. Silence Gap Checker - Detects unwanted silence gaps
4. Loudness Validator - Verifies loudness normalization

Uses FFmpeg for all audio analysis operations.
"""
import subprocess
import logging
import json
import re
import math
from pathlib import Path
from typing import Dict, Any, List, Literal, Optional
from dataclasses import dataclass, asdict, field


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation operations fail."""
    pass


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    passed: bool
    severity: Literal["PASS", "WARNING", "CRITICAL"]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ValidationReport:
    """Complete validation report for an audio file."""
    audio_file: str
    timestamp: str
    checks: Dict[str, ValidationResult]
    overall_passed: bool
    critical_issues: int
    warnings: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "audio_file": self.audio_file,
            "timestamp": self.timestamp,
            "checks": {k: v.to_dict() for k, v in self.checks.items()},
            "overall_passed": self.overall_passed,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings
        }
    
    def print_summary(self) -> None:
        """Print human-readable summary."""
        print("\n" + "=" * 70)
        print("AUDIO QUALITY VALIDATION REPORT")
        print("=" * 70)
        print(f"File: {self.audio_file}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Overall Status: {'✓ PASSED' if self.overall_passed else '✗ FAILED'}")
        print(f"Critical Issues: {self.critical_issues}")
        print(f"Warnings: {self.warnings}")
        print("\nDetailed Results:")
        print("-" * 70)
        
        for check_name, result in self.checks.items():
            icon = "✓" if result.passed else "✗"
            severity = f"[{result.severity}]"
            print(f"{icon} {check_name:25s} {severity:12s} {result.message}")
            
            # Print details if present
            if result.details:
                for key, value in result.details.items():
                    print(f"    {key}: {value}")
        
        print("=" * 70 + "\n")


class QualityValidator:
    """
    FFmpeg-based audio quality validator.
    
    Provides automated checks for common audio quality issues.
    """
    
    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
        dry_run: bool = False
    ):
        """
        Initialize quality validator.
        
        Args:
            ffmpeg_path: Path to FFmpeg executable
            ffprobe_path: Path to FFprobe executable
            dry_run: If True, only print commands without executing
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.dry_run = dry_run
        
        if not dry_run:
            self._validate_tools()
    
    def _validate_tools(self) -> None:
        """Validate FFmpeg and FFprobe are installed."""
        for tool, path in [("ffmpeg", self.ffmpeg_path), ("ffprobe", self.ffprobe_path)]:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    raise ValidationError(f"{tool} not found: {path}")
                logger.debug(f"{tool} version: {result.stdout.splitlines()[0]}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                raise ValidationError(f"{tool} not accessible: {e}")
    
    def _run_ffprobe(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run FFprobe command."""
        cmd = [self.ffprobe_path] + args
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, "{}", "")
        
        logger.debug(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result
        except subprocess.TimeoutExpired:
            raise ValidationError("FFprobe command timed out")
        except Exception as e:
            raise ValidationError(f"FFprobe execution failed: {e}")
    
    def _run_ffmpeg(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run FFmpeg command."""
        cmd = [self.ffmpeg_path] + args
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, "", "")
        
        logger.debug(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result
        except subprocess.TimeoutExpired:
            raise ValidationError("FFmpeg command timed out")
        except Exception as e:
            raise ValidationError(f"FFmpeg execution failed: {e}")
    
    def validate_duration(
        self,
        audio_path: Path,
        expected: float,
        tolerance: float = 0.5
    ) -> ValidationResult:
        """
        Validate audio duration matches expected value.
        
        Args:
            audio_path: Path to audio file
            expected: Expected duration in seconds
            tolerance: Acceptable deviation in seconds
            
        Returns:
            ValidationResult with duration check results
        """
        logger.info(f"Validating duration: {audio_path.name}")
        
        if not audio_path.exists():
            return ValidationResult(
                passed=False,
                severity="CRITICAL",
                message=f"Audio file not found: {audio_path}",
                details={}
            )
        
        # Get actual duration using ffprobe
        args = [
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio_path)
        ]
        
        result = self._run_ffprobe(args)
        
        if self.dry_run:
            actual = expected  # Mock for dry run
        else:
            try:
                data = json.loads(result.stdout)
                actual = float(data["format"]["duration"])
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                return ValidationResult(
                    passed=False,
                    severity="CRITICAL",
                    message=f"Failed to parse duration: {e}",
                    details={"stdout": result.stdout, "stderr": result.stderr}
                )
        
        deviation = abs(actual - expected)
        passed = deviation <= tolerance
        
        if passed:
            severity = "PASS"
            message = f"Duration matches expected ({actual:.2f}s vs {expected:.2f}s)"
        elif deviation <= tolerance * 2:
            severity = "WARNING"
            message = f"Duration slightly off ({actual:.2f}s vs {expected:.2f}s, Δ{deviation:.2f}s)"
        else:
            severity = "CRITICAL"
            message = f"Duration mismatch ({actual:.2f}s vs {expected:.2f}s, Δ{deviation:.2f}s)"
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            message=message,
            details={
                "expected_duration": f"{expected:.2f}s",
                "actual_duration": f"{actual:.2f}s",
                "deviation": f"{deviation:.2f}s",
                "tolerance": f"{tolerance:.2f}s"
            }
        )
    
    def detect_clipping(
        self,
        audio_path: Path,
        threshold: float = 0.99
    ) -> ValidationResult:
        """
        Detect audio clipping (samples exceeding threshold).
        
        Args:
            audio_path: Path to audio file
            threshold: Clipping threshold (0.0 to 1.0)
            
        Returns:
            ValidationResult with clipping detection results
        """
        logger.info(f"Detecting clipping: {audio_path.name}")
        
        if not audio_path.exists():
            return ValidationResult(
                passed=False,
                severity="CRITICAL",
                message=f"Audio file not found: {audio_path}",
                details={}
            )
        
        # Use astats filter to get peak levels
        args = [
            "-i", str(audio_path),
            "-af", "astats=metadata=1:reset=1",
            "-f", "null",
            "-"
        ]
        
        result = self._run_ffmpeg(args)
        
        if self.dry_run:
            max_level = 0.85  # Mock for dry run
        else:
            # Parse peak level from stderr
            max_level = 0.0
            for line in result.stderr.splitlines():
                # Look for "Peak level dB:" or "Overall Max level dB:"
                if "Max level dB:" in line or "Peak level dB:" in line:
                    try:
                        # Extract dB value and convert to linear
                        db_match = re.search(r'-?\d+\.?\d*', line)
                        if db_match:
                            db_value = float(db_match.group())
                            # Convert dB to linear scale (0dB = 1.0, -6dB ≈ 0.5)
                            linear_value = 10 ** (db_value / 20)
                            max_level = max(max_level, abs(linear_value))
                    except ValueError:
                        continue
        
        # If we couldn't parse, try alternative method
        if max_level == 0.0 and not self.dry_run:
            # Fall back to volumedetect
            args = [
                "-i", str(audio_path),
                "-af", "volumedetect",
                "-f", "null",
                "-"
            ]
            result = self._run_ffmpeg(args)
            
            for line in result.stderr.splitlines():
                if "max_volume:" in line:
                    try:
                        db_str = line.split("max_volume:")[1].split("dB")[0].strip()
                        db_value = float(db_str)
                        max_level = 10 ** (db_value / 20)
                    except (ValueError, IndexError):
                        continue
        
        clipping_detected = max_level >= threshold
        passed = not clipping_detected
        
        if passed:
            severity = "PASS"
            message = f"No clipping detected (peak: {max_level:.3f})"
        elif max_level < 1.0:
            severity = "WARNING"
            message = f"Near clipping detected (peak: {max_level:.3f})"
        else:
            severity = "CRITICAL"
            message = f"Clipping detected (peak: {max_level:.3f})"
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            message=message,
            details={
                "max_level": f"{max_level:.3f}",
                "threshold": f"{threshold:.3f}",
                "max_level_db": f"{20 * math.log10(max_level if max_level > 0 else 0.001):.2f}dB"
            }
        )
    
    def check_silence_gaps(
        self,
        audio_path: Path,
        max_silence: float = 2.0,
        silence_threshold: float = -30.0
    ) -> ValidationResult:
        """
        Check for unwanted silence gaps in audio.
        
        Args:
            audio_path: Path to audio file
            max_silence: Maximum acceptable silence duration in seconds
            silence_threshold: Silence detection threshold in dB
            
        Returns:
            ValidationResult with silence gap detection results
        """
        logger.info(f"Checking silence gaps: {audio_path.name}")
        
        if not audio_path.exists():
            return ValidationResult(
                passed=False,
                severity="CRITICAL",
                message=f"Audio file not found: {audio_path}",
                details={}
            )
        
        # Use silencedetect filter
        args = [
            "-i", str(audio_path),
            "-af", f"silencedetect=n={silence_threshold}dB:d={max_silence}",
            "-f", "null",
            "-"
        ]
        
        result = self._run_ffmpeg(args)
        
        if self.dry_run:
            silence_gaps = []
        else:
            # Parse silence gaps from stderr
            silence_gaps = []
            silence_start = None
            
            for line in result.stderr.splitlines():
                if "silence_start:" in line:
                    try:
                        silence_start = float(line.split("silence_start:")[1].strip())
                    except (ValueError, IndexError):
                        continue
                elif "silence_end:" in line and silence_start is not None:
                    try:
                        silence_end = float(line.split("silence_end:")[1].split("|")[0].strip())
                        duration = silence_end - silence_start
                        if duration > max_silence:
                            silence_gaps.append({
                                "start": silence_start,
                                "end": silence_end,
                                "duration": duration
                            })
                        silence_start = None
                    except (ValueError, IndexError):
                        continue
        
        passed = len(silence_gaps) == 0
        
        if passed:
            severity = "PASS"
            message = f"No excessive silence gaps detected"
        elif len(silence_gaps) <= 2:
            severity = "WARNING"
            message = f"Found {len(silence_gaps)} silence gap(s) > {max_silence}s"
        else:
            severity = "CRITICAL"
            message = f"Found {len(silence_gaps)} silence gaps > {max_silence}s"
        
        details = {
            "max_silence_threshold": f"{max_silence}s",
            "silence_threshold_db": f"{silence_threshold}dB",
            "gaps_found": len(silence_gaps)
        }
        
        if silence_gaps:
            details["silence_gaps"] = [
                {
                    "start": f"{gap['start']:.2f}s",
                    "end": f"{gap['end']:.2f}s",
                    "duration": f"{gap['duration']:.2f}s"
                }
                for gap in silence_gaps[:5]  # Show max 5 gaps
            ]
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            message=message,
            details=details
        )
    
    def validate_loudness(
        self,
        audio_path: Path,
        target: float = -14.0,
        tolerance: float = 1.0
    ) -> ValidationResult:
        """
        Validate loudness normalization (LUFS).
        
        Args:
            audio_path: Path to audio file
            target: Target loudness in LUFS
            tolerance: Acceptable deviation in LUFS
            
        Returns:
            ValidationResult with loudness validation results
        """
        logger.info(f"Validating loudness: {audio_path.name}")
        
        if not audio_path.exists():
            return ValidationResult(
                passed=False,
                severity="CRITICAL",
                message=f"Audio file not found: {audio_path}",
                details={}
            )
        
        # Use loudnorm filter with print_format=json
        args = [
            "-i", str(audio_path),
            "-af", "loudnorm=print_format=json",
            "-f", "null",
            "-"
        ]
        
        result = self._run_ffmpeg(args)
        
        if self.dry_run:
            actual_loudness = target  # Mock for dry run
        else:
            # Parse JSON from stderr
            try:
                # Find JSON block in stderr
                stderr_lines = result.stderr.splitlines()
                json_start = None
                
                for i, line in enumerate(stderr_lines):
                    if line.strip() == "{":
                        json_start = i
                        break
                
                if json_start is None:
                    raise ValueError("No JSON output found")
                
                json_lines = []
                for i in range(json_start, len(stderr_lines)):
                    json_lines.append(stderr_lines[i])
                    if stderr_lines[i].strip() == "}":
                        break
                
                json_str = "\n".join(json_lines)
                data = json.loads(json_str)
                
                actual_loudness = float(data["input_i"])
            except (json.JSONDecodeError, KeyError, ValueError, IndexError) as e:
                return ValidationResult(
                    passed=False,
                    severity="CRITICAL",
                    message=f"Failed to parse loudness data: {e}",
                    details={"stderr": result.stderr[:500]}
                )
        
        deviation = abs(actual_loudness - target)
        passed = deviation <= tolerance
        
        if passed:
            severity = "PASS"
            message = f"Loudness within target ({actual_loudness:.1f} LUFS vs {target:.1f} LUFS)"
        elif deviation <= tolerance * 2:
            severity = "WARNING"
            message = f"Loudness slightly off ({actual_loudness:.1f} LUFS vs {target:.1f} LUFS)"
        else:
            severity = "CRITICAL"
            message = f"Loudness out of range ({actual_loudness:.1f} LUFS vs {target:.1f} LUFS)"
        
        return ValidationResult(
            passed=passed,
            severity=severity,
            message=message,
            details={
                "target_loudness": f"{target:.1f} LUFS",
                "actual_loudness": f"{actual_loudness:.1f} LUFS",
                "deviation": f"{deviation:.1f} LUFS",
                "tolerance": f"{tolerance:.1f} LUFS"
            }
        )
    
    def validate_all(
        self,
        audio_path: Path,
        expected_duration: float,
        duration_tolerance: float = 0.5,
        clipping_threshold: float = 0.99,
        max_silence: float = 2.0,
        loudness_target: float = -14.0,
        loudness_tolerance: float = 1.0
    ) -> ValidationReport:
        """
        Run all validation checks and generate report.
        
        Args:
            audio_path: Path to audio file
            expected_duration: Expected duration in seconds
            duration_tolerance: Duration tolerance in seconds
            clipping_threshold: Clipping detection threshold
            max_silence: Maximum silence gap in seconds
            loudness_target: Target loudness in LUFS
            loudness_tolerance: Loudness tolerance in LUFS
            
        Returns:
            ValidationReport with all check results
        """
        from datetime import datetime
        
        logger.info(f"Running full validation suite on {audio_path.name}")
        
        checks = {}
        
        # Run all checks
        checks["duration"] = self.validate_duration(audio_path, expected_duration, duration_tolerance)
        checks["clipping"] = self.detect_clipping(audio_path, clipping_threshold)
        checks["silence_gaps"] = self.check_silence_gaps(audio_path, max_silence)
        checks["loudness"] = self.validate_loudness(audio_path, loudness_target, loudness_tolerance)
        
        # Analyze results
        critical_issues = sum(1 for check in checks.values() if check.severity == "CRITICAL")
        warnings = sum(1 for check in checks.values() if check.severity == "WARNING")
        overall_passed = all(check.passed for check in checks.values())
        
        report = ValidationReport(
            audio_file=str(audio_path),
            timestamp=datetime.utcnow().isoformat(),
            checks=checks,
            overall_passed=overall_passed,
            critical_issues=critical_issues,
            warnings=warnings
        )
        
        logger.info(f"Validation complete: {'PASSED' if overall_passed else 'FAILED'}")
        logger.info(f"  Critical issues: {critical_issues}")
        logger.info(f"  Warnings: {warnings}")
        
        return report


def load_timing_data(timing_file: Path) -> float:
    """
    Load expected duration from timing.json.
    
    Args:
        timing_file: Path to timing.json
        
    Returns:
        Total expected duration in seconds
    """
    with open(timing_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("total_duration", 0.0)
