#!/usr/bin/env python3
"""
Test parser with the actual format from the user's output
"""

# This is the exact format the user showed
actual_output = """ACTION ITEMS
------------------------------
Task: 
Owner: ---
Deadline: ---"""

def parse_action_items(text):
    """Parse action items from the actual format"""
    lines = text.strip().split('\n')
    
    action_items = []
    current_action = {}
    in_actions = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            # Empty line might signal end of an action item
            if current_action and in_actions:
                # Only add if task is not empty
                task = current_action.get("task", "").strip()
                if task and task != "":
                    action_items.append({
                        "task": task,
                        "owner": current_action.get("owner", "Team"),
                        "deadline": current_action.get("deadline")
                    })
                current_action = {}
            continue
        
        # Check if we're in action items section
        if "ACTION ITEM" in line.upper():
            in_actions = True
            continue
        
        # Skip separator lines
        if line.startswith("---") or line.startswith("==="):
            continue
        
        if in_actions:
            if line.startswith("Task:"):
                # Save previous action if exists
                if current_action.get("task", "").strip():
                    action_items.append({
                        "task": current_action["task"],
                        "owner": current_action.get("owner", "Team"),
                        "deadline": current_action.get("deadline")
                    })
                # Start new action
                task_text = line[5:].strip()
                # Skip if task is empty or just whitespace
                if task_text and task_text != "":
                    current_action = {"task": task_text}
                else:
                    current_action = {}
            elif line.startswith("Owner:"):
                if current_action:
                    owner_text = line[6:].strip()
                    # Convert "---" or empty to "Team"
                    current_action["owner"] = owner_text if owner_text and owner_text != "---" else "Team"
            elif line.startswith(("Deadline:", "Due:")):
                if current_action:
                    deadline_text = line.split(":", 1)[1].strip()
                    # Convert "---" or empty to None
                    current_action["deadline"] = deadline_text if deadline_text and deadline_text != "---" else None
    
    # Don't forget the last action item if valid
    if current_action and current_action.get("task", "").strip():
        action_items.append({
            "task": current_action["task"],
            "owner": current_action.get("owner", "Team"),
            "deadline": current_action.get("deadline")
        })
    
    return action_items

# Test with the actual problematic output
print("Testing with actual output format:")
print("="*50)
print(actual_output)
print("="*50)

result = parse_action_items(actual_output)
print(f"\nParsed {len(result)} action items:")
for i, item in enumerate(result, 1):
    print(f"  {i}. Task: '{item['task']}'")
    print(f"     Owner: {item['owner']}")
    print(f"     Deadline: {item['deadline'] or 'Not specified'}")

if len(result) == 0:
    print("\n❌ No action items parsed - this explains the empty tasks in Notion!")
    print("The issue: Task field is empty in the output")

# Test with a good example
good_example = """ACTION ITEMS
------------------------------
Task: Align sales processes for building scenarios
Owner: Sales Team
Deadline: Next week

Task: Develop risk management plan
Owner: Operations
Deadline: ---"""

print("\n" + "="*50)
print("Testing with properly formatted action items:")
print("="*50)
print(good_example)
print("="*50)

good_result = parse_action_items(good_example)
print(f"\nParsed {len(good_result)} action items:")
for i, item in enumerate(good_result, 1):
    print(f"  {i}. Task: '{item['task']}'")
    print(f"     Owner: {item['owner']}")
    print(f"     Deadline: {item['deadline'] or 'Not specified'}")

if len(good_result) > 0:
    print("\n✅ Successfully parsed action items when properly formatted")