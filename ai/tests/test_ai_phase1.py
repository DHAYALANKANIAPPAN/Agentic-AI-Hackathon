import pytest
from unittest.mock import patch, MagicMock
from ai.core import analyze_profile, find_gaps
from shared.schemas.models import SkillProfile, Skill, SkillLevel, GapList, GapStatus

def test_analyze_profile_calls_llm():
    with patch('ai.llm.generate_json') as mock_generate_json:
        mock_generate_json.return_value = SkillProfile(
            skills=[Skill(name="Python", level=SkillLevel.INTERMEDIATE, evidence="Built APIs")]
        )
        
        profile = analyze_profile("I am a dev", ["Doc 1 text"])
        assert len(profile.skills) == 1
        assert profile.skills[0].name == "Python"
        assert mock_generate_json.call_count == 1

def test_find_gaps_calls_llm():
    with patch('ai.llm.generate_json') as mock_generate_json:
        mock_generate_json.return_value = GapList(target_role="Data Scientist", gaps=[])
        
        profile = SkillProfile()
        gaps = find_gaps(profile, "Data Scientist")
        
        assert gaps.target_role == "Data Scientist"
        assert mock_generate_json.call_count == 1

def test_find_gaps_fallback():
    with patch('ai.llm.generate_json') as mock_generate_json:
        mock_generate_json.side_effect = ValueError("LLM Error")
        
        profile = SkillProfile()
        gaps = find_gaps(profile, "Data Scientist")
        
        # Should hit fallback
        assert gaps.target_role == "Data Scientist"
        assert len(gaps.gaps) > 0
        assert gaps.gaps[0].required_skill == "Python"
