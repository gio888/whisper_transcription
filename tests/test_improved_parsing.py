#!/usr/bin/env python3
"""
Test the improved parsing with fallback extraction
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_analyzer import MeetingAnalyzer

# Simulate a response with empty action items but good decisions
test_response = """
## Summary of the Meeting
The main topics discussed were the partnership between Philcom and Rice, focusing on sales processes and risk management.

## Key Decisions
• Philcom and Rice will further discuss and align on their respective sales processes
• Philcom is open to the DTC model where Rice is the partner
• Both parties agreed to establish transparency protocols with building administration

## Notable Discussion Points
• There was a debate around the level of transparency required with the building administration
• Concerns were raised about potential risks with last mile partners
• The team discussed the need for better alignment on sales processes

## Action Items
Task: 
Owner: ---
Deadline: ---
"""

# Test the parser
analyzer = MeetingAnalyzer()
result = analyzer._parse_analysis_response(test_response)

print("=== PARSING RESULTS ===")
print(f"\nSummary: {result.summary[:100]}...")
print(f"\nKey Decisions: {len(result.key_decisions)} items")
for i, decision in enumerate(result.key_decisions, 1):
    print(f"  {i}. {decision}")

print(f"\nDiscussion Points: {len(result.discussion_points)} items")
for i, point in enumerate(result.discussion_points, 1):
    print(f"  {i}. {point}")

print(f"\nAction Items: {len(result.action_items)} items")
if result.action_items:
    for i, item in enumerate(result.action_items, 1):
        print(f"  {i}. Task: {item.task}")
        print(f"     Owner: {item.owner}")
        print(f"     Deadline: {item.deadline}")
    print("\n✅ SUCCESS: Fallback extraction created action items from decisions/discussions!")
else:
    print("\n❌ PROBLEM: Still no action items even with fallback extraction")