"""
Music Generator Agent.

Generates scene-based music prompts and validates downloaded music files.
"""
from .generator import generate_music, MusicGenerator

__version__ = "0.1.0"
__all__ = ['generate_music', 'MusicGenerator']
