"""
State management for audio generation pipeline.

Tracks progress, enables resume capability, and manages concurrent access.
State is persisted as JSON after each successful operation.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


class StateError(Exception):
    """Raised when state operations fail."""
    pass


@dataclass
class PhaseStatus:
    """Status of a pipeline phase."""
    name: str
    status: str  # "pending", "in_progress", "complete", "failed"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class State:
    """
    Audio generation pipeline state.
    
    Attributes:
        story: Story name
        last_updated: ISO timestamp of last update
        phases: Status of each pipeline phase
        voice_clips: Status of individual voice clips {filename: status}
        music_files: Status of music files {filename: status}
        total_cost: Total cost incurred (USD)
        estimated_remaining: Estimated remaining cost (USD)
        metadata: Additional metadata
    """
    story: str
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    phases: Dict[str, str] = field(default_factory=lambda: {
        "timing": "pending",
        "music": "pending",
        "voices": "pending",
        "mix": "pending",
        "validate": "pending"
    })
    voice_clips: Dict[str, str] = field(default_factory=dict)
    music_files: Dict[str, str] = field(default_factory=dict)
    total_cost: float = 0.0
    estimated_remaining: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "State":
        """Create state from dictionary."""
        return cls(**data)


class StateManager:
    """
    Manages state persistence and concurrent access.
    
    Example:
        >>> manager = StateManager("stories/luna/audio/progress.json")
        >>> if manager.exists():
        ...     manager.load()
        ... else:
        ...     manager.initialize("luna")
        >>> manager.update_phase("timing", "complete")
        >>> manager.save()
    """
    
    def __init__(self, state_file: Path):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file (e.g., progress.json)
        """
        self.state_file = Path(state_file)
        self.state: Optional[State] = None
    
    def exists(self) -> bool:
        """Check if state file exists."""
        return self.state_file.exists()
    
    def initialize(self, story: str) -> State:
        """
        Initialize new state for a story.
        
        Args:
            story: Story name
            
        Returns:
            New State object
            
        Example:
            >>> manager = StateManager("progress.json")
            >>> state = manager.initialize("luna-y-la-estrella-perdida")
        """
        self.state = State(story=story)
        self._ensure_directory()
        self.save()
        logger.info(f"Initialized state for story: {story}")
        return self.state
    
    def load(self) -> State:
        """
        Load state from file.
        
        Returns:
            Loaded State object
            
        Raises:
            StateError: If state file is corrupt or cannot be read
            
        Example:
            >>> manager = StateManager("progress.json")
            >>> state = manager.load()
            >>> print(state.story)
        """
        if not self.exists():
            raise StateError(f"State file not found: {self.state_file}")
        
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.state = State.from_dict(data)
            logger.info(f"Loaded state for story: {self.state.story}")
            return self.state
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise StateError(f"Failed to load state: {e}")
    
    def save(self) -> None:
        """
        Save current state to file.
        
        Raises:
            StateError: If state is not initialized or save fails
            
        Example:
            >>> manager.update_phase("timing", "complete")
            >>> manager.save()
        """
        if self.state is None:
            raise StateError("State not initialized. Call initialize() or load() first.")
        
        # Update timestamp
        self.state.last_updated = datetime.utcnow().isoformat()
        
        self._ensure_directory()
        
        try:
            # Write atomically: write to temp file, then rename
            temp_file = self.state_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.state_file)
            logger.debug(f"Saved state to {self.state_file}")
        except (OSError, IOError) as e:
            raise StateError(f"Failed to save state: {e}")
    
    def update_phase(self, phase: str, status: str, error: Optional[str] = None) -> None:
        """
        Update phase status.
        
        Args:
            phase: Phase name (timing, music, voices, mix, validate)
            status: New status (pending, in_progress, complete, failed)
            error: Optional error message
            
        Example:
            >>> manager.update_phase("timing", "complete")
            >>> manager.update_phase("voices", "failed", error="API rate limit")
        """
        if self.state is None:
            raise StateError("State not initialized")
        
        self.state.phases[phase] = status
        
        if error:
            self.state.metadata[f"{phase}_error"] = error
        
        logger.info(f"Phase {phase} → {status}")
    
    def update_voice_clip(self, filename: str, status: str) -> None:
        """
        Update voice clip status.
        
        Args:
            filename: Voice clip filename (e.g., "narrator_1A.mp3")
            status: Status (pending, generating, complete, failed)
            
        Example:
            >>> manager.update_voice_clip("luna_3B.mp3", "complete")
        """
        if self.state is None:
            raise StateError("State not initialized")
        
        self.state.voice_clips[filename] = status
    
    def update_music_file(self, filename: str, status: str) -> None:
        """
        Update music file status.
        
        Args:
            filename: Music filename (e.g., "scene_1.mp3")
            status: Status (pending, downloaded, validated, failed)
            
        Example:
            >>> manager.update_music_file("scene_1.mp3", "validated")
        """
        if self.state is None:
            raise StateError("State not initialized")
        
        self.state.music_files[filename] = status
    
    def add_cost(self, amount: float) -> None:
        """
        Add to total cost.
        
        Args:
            amount: Cost in USD to add
            
        Example:
            >>> manager.add_cost(1.25)  # $1.25 for voice clip
        """
        if self.state is None:
            raise StateError("State not initialized")
        
        self.state.total_cost += amount
        logger.debug(f"Added cost: ${amount:.2f}, total: ${self.state.total_cost:.2f}")
    
    def set_estimated_remaining(self, amount: float) -> None:
        """
        Set estimated remaining cost.
        
        Args:
            amount: Estimated remaining cost in USD
            
        Example:
            >>> manager.set_estimated_remaining(8.50)
        """
        if self.state is None:
            raise StateError("State not initialized")
        
        self.state.estimated_remaining = amount
    
    def get_completed_clips(self) -> list[str]:
        """
        Get list of completed voice clip filenames.
        
        Returns:
            List of filenames with status "complete"
            
        Example:
            >>> completed = manager.get_completed_clips()
            >>> print(f"Completed: {len(completed)} clips")
        """
        if self.state is None:
            return []
        
        return [
            filename for filename, status in self.state.voice_clips.items()
            if status == "complete"
        ]
    
    def get_failed_clips(self) -> list[str]:
        """
        Get list of failed voice clip filenames.
        
        Returns:
            List of filenames with status "failed"
        """
        if self.state is None:
            return []
        
        return [
            filename for filename, status in self.state.voice_clips.items()
            if status == "failed"
        ]
    
    def _ensure_directory(self) -> None:
        """Create state file directory if it doesn't exist."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
