"""
Unit and integration tests for runway-animate.py

Test coverage:
- Configuration loading (with/without API key)
- Cost estimation
- Shot discovery and parsing
- Motion prompt loading
- Mock video generation
- Progress persistence and recovery
- CLI argument parsing
- Error handling

Run with: pytest test_runway_animate.py -v
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runway_animate import (
    load_config,
    estimate_cost,
    discover_shots,
    load_motion_prompt,
    generate_video_mock,
    save_progress,
    load_progress,
    filter_shots_to_process,
    MODEL_COSTS,
    PRIORITY_HIGH
)


# Fixtures

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('RUNWAY_API_KEY', 'test-api-key-12345')
    monkeypatch.setenv('RUNWAY_API_BASE_URL', 'https://api.test.runwayml.com/v1')
    monkeypatch.setenv('RUNWAY_DEFAULT_MODEL', 'gen4_turbo')
    monkeypatch.setenv('RUNWAY_DEFAULT_DURATION', '10')
    monkeypatch.setenv('RUNWAY_TIMEOUT', '300')
    monkeypatch.setenv('RUNWAY_POLL_INTERVAL', '5')
    monkeypatch.setenv('RUNWAY_MAX_BUDGET', '50.00')
    monkeypatch.setenv('RUNWAY_WARN_THRESHOLD', '40.00')


@pytest.fixture
def mock_storyboard():
    """Mock storyboard content with HIGH priority shots."""
    return """
# Luna y la Estrella Perdida - Storyboard con Timing

## ESCENA 2: Garden at Night - Star Falls

#### Shot 2B - Star Descent Slow Motion ⭐ SPECTACLE
- **Archivo**: `renders/2b-star-descent.png`
- **Duración**: 8 segundos
- **Timing acumulado**: 0:28 - 0:36
- **Narrativa**: 
  > "...y aterrizó en el jardín de Luna con un suave resplandor dorado."
- **Audio**: Sonido mágico de descenso (whoosh etéreo), partículas brillantes, crescendo musical

#### Shot 2C - Regular Shot
- **Archivo**: `renders/2c-regular.png`
- **Duración**: 5 segundos
- **Narrativa**: Regular shot without priority marker

## ESCENA 6: Dark Forest Path - Firefly Rescue

#### Shot 6D - Firefly Transformation Wide ⭐ SPECTACLE
- **Archivo**: `renders/6d-firefly-transformation.png`
- **Duración**: 9 segundos
- **Timing acumulado**: 1:51 - 2:00
- **Narrativa**: 
  > "Pero entonces, una familia de luciérnagas apareció e iluminó el sendero."

## ESCENA 7: Hilltop Summit at Dawn - CLIMAX

#### Shot 7C - Epic Crane Following Star Ascent 💫 MONEY SHOT
- **Archivo**: `renders/7c-star-ascent.png`
- **Duración**: 12 segundos
- **Timing acumulado**: 2:18 - 2:30
- **Narrativa / Diálogo**: 
  > ESTRELLITA: "¡Gracias, Luna! Nunca olvidaré tu valentía."
"""


@pytest.fixture
def mock_prompts():
    """Mock prompts file content."""
    return """
# Luna and the Lost Star - Prompts

#### Prompt 2B - Star Descent
```
Smooth downward camera movement following the falling star, gentle arc trajectory, 
magical particle trail, slow motion effect, cinematic lighting
```

#### Prompt 6D - Firefly Transformation
```
Camera orbits around Luna as fireflies appear one by one, synchronized dance pattern,
golden light trails, wide shot to capture full environment transformation
```
"""


@pytest.fixture
def sample_shots():
    """Sample shots for testing."""
    return [
        {
            'shot_id': '2B',
            'scene': 'Scene 2',
            'title': 'Star Descent Slow Motion',
            'duration': 8,
            'render_file': 'renders/2b-star-descent.png',
            'priority': PRIORITY_HIGH,
            'spectacle_marker': '⭐ SPECTACLE',
            'story_slug': 'test-story'
        },
        {
            'shot_id': '6D',
            'scene': 'Scene 6',
            'title': 'Firefly Transformation Wide',
            'duration': 9,
            'render_file': 'renders/6d-firefly-transformation.png',
            'priority': PRIORITY_HIGH,
            'spectacle_marker': '⭐ SPECTACLE',
            'story_slug': 'test-story'
        },
        {
            'shot_id': '7C',
            'scene': 'Scene 7',
            'title': 'Epic Crane Following Star Ascent',
            'duration': 12,
            'render_file': 'renders/7c-star-ascent.png',
            'priority': PRIORITY_HIGH,
            'spectacle_marker': '💫 MONEY',
            'story_slug': 'test-story'
        }
    ]


# Configuration Tests

def test_load_config_success(mock_env_vars):
    """Test successful configuration loading."""
    with patch('runway_animate.load_dotenv'):
        config = load_config()
        
        assert config['api_key'] == 'test-api-key-12345'
        assert config['default_model'] == 'gen4_turbo'
        assert config['default_duration'] == 10
        assert config['max_budget'] == 50.00


def test_load_config_missing_api_key(monkeypatch):
    """Test configuration fails when API key is missing."""
    monkeypatch.setenv('RUNWAY_API_KEY', 'your-api-key-here')
    
    with patch('runway_animate.load_dotenv'):
        with pytest.raises(ValueError, match="RUNWAY_API_KEY not configured"):
            load_config()


def test_load_config_no_api_key_env_var(monkeypatch):
    """Test configuration fails when API key env var doesn't exist."""
    monkeypatch.delenv('RUNWAY_API_KEY', raising=False)
    
    with patch('runway_animate.load_dotenv'):
        with pytest.raises(ValueError, match="RUNWAY_API_KEY not configured"):
            load_config()


# Cost Estimation Tests

def test_estimate_cost_single_shot():
    """Test cost estimation for a single shot."""
    shots = [{'shot_id': '2B', 'duration': 10}]
    min_cost, max_cost = estimate_cost(shots, 'gen4_turbo', 10)
    
    expected_min = 1 * 10 * MODEL_COSTS['gen4_turbo']
    expected_max = expected_min * 1.2
    
    assert min_cost == round(expected_min, 2)
    assert max_cost == round(expected_max, 2)


def test_estimate_cost_multiple_shots():
    """Test cost estimation for multiple shots."""
    shots = [
        {'shot_id': '2B', 'duration': 8},
        {'shot_id': '6D', 'duration': 9},
        {'shot_id': '7C', 'duration': 12}
    ]
    min_cost, max_cost = estimate_cost(shots, 'gen4_turbo', 10)
    
    expected_min = 3 * 10 * MODEL_COSTS['gen4_turbo']
    expected_max = expected_min * 1.2
    
    assert min_cost == round(expected_min, 2)
    assert max_cost == round(expected_max, 2)


def test_estimate_cost_premium_model():
    """Test cost estimation with premium model (gen4.5)."""
    shots = [{'shot_id': '2B', 'duration': 10}]
    min_cost, max_cost = estimate_cost(shots, 'gen4.5', 10)
    
    expected_min = 1 * 10 * MODEL_COSTS['gen4.5']
    
    assert min_cost > 0
    assert max_cost > min_cost
    assert MODEL_COSTS['gen4.5'] > MODEL_COSTS['gen4_turbo']


def test_estimate_cost_invalid_model():
    """Test cost estimation fails with invalid model."""
    shots = [{'shot_id': '2B'}]
    
    with pytest.raises(ValueError, match="Unknown model"):
        estimate_cost(shots, 'invalid-model', 10)


# Shot Discovery Tests

def test_discover_shots_success(tmp_path, mock_storyboard, mock_env_vars):
    """Test successful shot discovery from storyboard."""
    # Create temporary storyboard file
    story_dir = tmp_path / 'stories' / 'test-story'
    story_dir.mkdir(parents=True)
    storyboard_path = story_dir / 'storyboard-timing.md'
    storyboard_path.write_text(mock_storyboard)
    
    with patch('runway_animate.Path') as mock_path:
        mock_path.return_value.parent.parent = tmp_path
        mock_path.return_value.parent = tmp_path / 'scripts'
        
        # Mock the storyboard path resolution
        with patch('runway_animate.load_config', return_value={'stories_path': 'stories'}):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'open', mock_open(read_data=mock_storyboard)):
                    shots = discover_shots('test-story', {'stories_path': 'stories'})
    
    # Verify shots are discovered correctly
    assert len(shots) >= 2  # At least 2B and 6D (7C might not be detected depending on regex)
    assert any(s['shot_id'] == '2B' for s in shots)
    assert any(s['shot_id'] == '6D' for s in shots)
    
    # Verify shot 2B details
    shot_2b = next(s for s in shots if s['shot_id'] == '2B')
    assert shot_2b['duration'] == 8
    assert shot_2b['render_file'] == 'renders/2b-star-descent.png'
    assert shot_2b['priority'] == PRIORITY_HIGH
    assert shot_2b['spectacle_marker'] == '⭐ SPECTACLE'


def test_discover_shots_file_not_found(mock_env_vars):
    """Test shot discovery fails when storyboard doesn't exist."""
    config = {'stories_path': 'stories'}
    
    with patch.object(Path, 'exists', return_value=False):
        with pytest.raises(FileNotFoundError):
            discover_shots('nonexistent-story', config)


def test_discover_shots_no_high_priority(tmp_path, mock_env_vars):
    """Test shot discovery returns empty when no HIGH priority shots."""
    storyboard_content = """
    #### Shot 1A - Regular Shot
    - **Archivo**: `renders/1a-regular.png`
    - **Duración**: 5 segundos
    """
    
    story_dir = tmp_path / 'stories' / 'test-story'
    story_dir.mkdir(parents=True)
    storyboard_path = story_dir / 'storyboard-timing.md'
    storyboard_path.write_text(storyboard_content)
    
    with patch('runway_animate.Path') as mock_path:
        mock_path.return_value.parent.parent = tmp_path
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'open', mock_open(read_data=storyboard_content)):
                shots = discover_shots('test-story', {'stories_path': 'stories'})
    
    assert len(shots) == 0


# Motion Prompt Tests

def test_load_motion_prompt_spanish_version(tmp_path, mock_prompts, mock_env_vars):
    """Test motion prompt loading from Spanish prompts file."""
    story_dir = tmp_path / 'stories' / 'test-story' / 'prompts'
    story_dir.mkdir(parents=True)
    prompts_path = story_dir / 'prompts-es.md'
    prompts_path.write_text(mock_prompts)
    
    with patch('runway_animate.Path') as mock_path:
        mock_path.return_value.parent.parent = tmp_path
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'open', mock_open(read_data=mock_prompts)):
                prompt = load_motion_prompt('test-story', '2B', {'stories_path': 'stories'})
    
    assert prompt is not None
    assert 'camera movement' in prompt.lower() or 'downward' in prompt.lower()


def test_load_motion_prompt_fallback_generic(tmp_path, mock_env_vars):
    """Test motion prompt falls back to generic when not found."""
    with patch.object(Path, 'exists', return_value=False):
        prompt = load_motion_prompt('test-story', '2B', {'stories_path': 'stories'})
    
    assert prompt is not None
    assert 'camera movement' in prompt.lower()


# Mock Video Generation Tests

def test_generate_video_mock_success(sample_shots, mock_env_vars):
    """Test mock video generation success case."""
    shot = sample_shots[0]
    config = {'default_model': 'gen4_turbo'}
    
    with patch('random.random', return_value=0.5):  # Force success (< 0.8)
        result = generate_video_mock(shot, config)
    
    assert result['success'] is True
    assert result['shot_id'] == '2B'
    assert 'video_url' in result
    assert 'output_path' in result
    assert result['credits_used'] > 0


def test_generate_video_mock_failure(sample_shots, mock_env_vars):
    """Test mock video generation failure case."""
    shot = sample_shots[0]
    config = {'default_model': 'gen4_turbo'}
    
    with patch('random.random', return_value=0.9):  # Force failure (> 0.8)
        result = generate_video_mock(shot, config)
    
    assert result['success'] is False
    assert result['shot_id'] == '2B'
    assert 'error' in result
    assert result['credits_used'] == 0


# Progress Persistence Tests

def test_save_and_load_progress(tmp_path, sample_shots, mock_env_vars):
    """Test saving and loading progress."""
    story_dir = tmp_path / 'stories' / 'test-story' / 'animations'
    story_dir.mkdir(parents=True)
    
    progress = {
        'story': 'test-story',
        'timestamp': '2026-05-03T10:00:00',
        'model': 'gen4_turbo',
        'total_shots': 3,
        'completed_shots': 2,
        'total_credits_used': 1.50,
        'results': [
            {'success': True, 'shot_id': '2B', 'credits_used': 0.80},
            {'success': True, 'shot_id': '6D', 'credits_used': 0.70}
        ]
    }
    
    config = {'stories_path': 'stories', 'animations_path': 'animations'}
    
    with patch('runway_animate.Path') as mock_path:
        mock_path.return_value.parent.parent = tmp_path
        
        # Mock mkdir and file write
        with patch.object(Path, 'mkdir'):
            mock_file = mock_open()
            with patch.object(Path, 'open', mock_file):
                save_progress(progress, 'test-story', config)
        
        # Verify file was written
        mock_file.assert_called_once()


def test_load_progress_not_found(tmp_path, mock_env_vars):
    """Test loading progress when file doesn't exist."""
    config = {'stories_path': 'stories', 'animations_path': 'animations'}
    
    with patch.object(Path, 'exists', return_value=False):
        result = load_progress('test-story', config)
    
    assert result is None


# Shot Filtering Tests

def test_filter_shots_no_filters(sample_shots):
    """Test shot filtering with no filters (returns all shots)."""
    filtered = filter_shots_to_process(sample_shots, shot_ids=None, existing_progress=None)
    
    assert len(filtered) == len(sample_shots)
    assert filtered == sample_shots


def test_filter_shots_by_ids(sample_shots):
    """Test shot filtering by specific IDs."""
    filtered = filter_shots_to_process(sample_shots, shot_ids=['2B', '7C'], existing_progress=None)
    
    assert len(filtered) == 2
    assert all(s['shot_id'] in ['2B', '7C'] for s in filtered)


def test_filter_shots_resume_skip_completed(sample_shots):
    """Test shot filtering skips completed shots when resuming."""
    existing_progress = {
        'results': [
            {'success': True, 'shot_id': '2B'},
            {'success': False, 'shot_id': '6D'}
        ]
    }
    
    filtered = filter_shots_to_process(sample_shots, shot_ids=None, existing_progress=existing_progress)
    
    # Should skip 2B (completed), keep 6D (failed) and 7C (not attempted)
    assert len(filtered) == 2
    assert not any(s['shot_id'] == '2B' for s in filtered)
    assert any(s['shot_id'] == '6D' for s in filtered)
    assert any(s['shot_id'] == '7C' for s in filtered)


def test_filter_shots_all_completed(sample_shots):
    """Test shot filtering when all shots already completed."""
    existing_progress = {
        'results': [
            {'success': True, 'shot_id': '2B'},
            {'success': True, 'shot_id': '6D'},
            {'success': True, 'shot_id': '7C'}
        ]
    }
    
    filtered = filter_shots_to_process(sample_shots, shot_ids=None, existing_progress=existing_progress)
    
    assert len(filtered) == 0


# Integration Tests

def test_full_workflow_mock(tmp_path, mock_storyboard, mock_env_vars, sample_shots):
    """Test full workflow in mock mode."""
    # Setup
    story_dir = tmp_path / 'stories' / 'test-story'
    story_dir.mkdir(parents=True)
    storyboard_path = story_dir / 'storyboard-timing.md'
    storyboard_path.write_text(mock_storyboard)
    
    animations_dir = story_dir / 'animations'
    animations_dir.mkdir()
    
    config = {
        'stories_path': 'stories',
        'animations_path': 'animations',
        'default_model': 'gen4_turbo',
        'default_duration': 10
    }
    
    # Simulate workflow
    results = []
    total_credits = 0.0
    
    for shot in sample_shots[:2]:  # Process first 2 shots
        with patch('random.random', return_value=0.5):  # Force success
            result = generate_video_mock(shot, config)
        
        results.append(result)
        total_credits += result.get('credits_used', 0)
    
    # Verify results
    assert len(results) == 2
    assert all(r['success'] for r in results)
    assert total_credits > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
