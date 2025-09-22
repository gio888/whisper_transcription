#!/usr/bin/env python3
"""
Test the get_analysis method to see if it properly loads cleaned_transcript
"""
import asyncio
import json
from meeting_analyzer import MeetingAnalyzer

async def test_get_analysis():
    """Test if get_analysis properly loads the cleaned transcript"""
    
    analyzer = MeetingAnalyzer()
    analysis_id = "analysis_test_fallback_001_20250910_163407"
    
    print(f"Testing get_analysis for: {analysis_id}")
    
    # Get analysis using the proper method
    analysis_data = await analyzer.get_analysis(analysis_id)
    
    if not analysis_data:
        print("ERROR: No analysis data returned")
        return
    
    print(f"\n=== ANALYSIS DATA FROM get_analysis() ===")
    print(f"Fields: {list(analysis_data.keys())}")
    
    # Check cleaned transcript
    cleaned_transcript = analysis_data.get('cleaned_transcript', '')
    print(f"\nCleaned Transcript: {'PRESENT' if cleaned_transcript else 'MISSING'}")
    if cleaned_transcript:
        print(f"  Length: {len(cleaned_transcript)} chars")
        print(f"  Preview: {cleaned_transcript[:100]}...")
    else:
        print("  ERROR: cleaned_transcript field is missing!")
    
    # Test with the format_meeting_content function from our debug script
    print(f"\n=== TESTING NOTION CONTENT GENERATION ===")
    
    # Simulate what notion_sync._format_meeting_content would do
    transcript_content = analysis_data.get("cleaned_transcript", "")
    if transcript_content:
        print(f"Transcript content for Notion toggle: {len(transcript_content[:2000])} chars")
        print(f"Preview: {transcript_content[:100]}...")
    else:
        print("ERROR: No transcript content for Notion toggle!")
    
    # Compare with direct JSON loading (what we found before)
    print(f"\n=== COMPARISON WITH DIRECT JSON LOADING ===")
    with open('analysis_results/analysis_test_fallback_001_20250910_163407.json', 'r') as f:
        direct_json = json.load(f)
    
    print(f"Direct JSON fields: {list(direct_json.keys())}")
    print(f"Direct JSON has cleaned_transcript: {'cleaned_transcript' in direct_json}")
    print(f"get_analysis() has cleaned_transcript: {'cleaned_transcript' in analysis_data}")

if __name__ == "__main__":
    asyncio.run(test_get_analysis())