#!/usr/bin/env python3
"""
Test script demonstrating the session update workflow.
Shows how users can update their information after calling /end.
"""
import json
from pathlib import Path
from app.memory import SessionStore
from app.schemas import Analytics
from app.config import DATA_DIR


def test_session_update_workflow():
    """Demonstrate the complete session update workflow."""
    print("=" * 70)
    print("WORKFLOW: User Updates Information After Session Ends")
    print("=" * 70)
    
    store = SessionStore()
    session_id = "test-user-456"
    
    # Step 1: Build conversation
    print("\n[STEP 1] User has conversation")
    store.append(session_id, {"role": "user", "content": "2 BHK dekhna hai"})
    store.append(session_id, {"role": "assistant", "content": "2 BHK available from 1.35 crore"})
    store.append(session_id, {"role": "user", "content": "Budget kaafi tight hai"})
    store.append(session_id, {"role": "assistant", "content": "EMI options hain..."})
    print(f"✓ Conversation has {len(store.history(session_id))} messages")
    
    # Step 2: End conversation and save analytics
    print("\n[STEP 2] User calls /end - Analytics extracted and saved")
    store.mark_ended(session_id)
    initial_analytics = {
        "language": "hinglish",
        "configuration": "2bhk",
        "budget": "tight",
        "interest_level": "warm",
        "site_visit_status": "not_requested",
        "follow_up_required": True,
        "objections": ["budget"],
        "outcome": "browsing",
        "opted_out": False,
        "escalated": False,
        "callback_time": None,
        "notes": "Customer has budget concerns but interested in 2BHK"
    }
    store.set_analytics(session_id, initial_analytics)
    print("✓ Session marked as ended")
    print("✓ Analytics saved to JSON file")
    
    # Step 3: User realizes they want to add more info
    print("\n[STEP 3] User wants to update - reopen session")
    store.reopen_session(session_id)
    print("✓ Session reopened for updates")
    print(f"  Session ended status: {store.is_ended(session_id)}")
    
    # Step 4: Option A - Continue chatting
    print("\n[STEP 4A] Option: User adds more context via chat")
    store.append(session_id, {"role": "user", "content": "Actually, I can check with my family about budget"})
    store.append(session_id, {"role": "assistant", "content": "Good! Let's discuss financing options"})
    print(f"✓ Conversation updated to {len(store.history(session_id))} messages")
    
    # Step 5: Option B - Directly update analytics
    print("\n[STEP 5B] Option: Manually update analytics")
    updates = {
        "interest_level": "hot",
        "budget": "1.5 - 2 crore",
        "objections": [],  # budget concern resolved
    }
    store.set_analytics(session_id, {**initial_analytics, **updates})
    print("✓ Analytics updated with manual corrections")
    
    # Step 6: Retrieve all session data
    print("\n[STEP 6] Retrieve complete session data")
    session_data = store.get_session_data(session_id)
    print(f"✓ Session data retrieved:")
    print(f"  - Messages: {len(session_data['messages'])}")
    print(f"  - Ended: {session_data['ended']}")
    print(f"  - Analytics available: {session_data['analytics'] is not None}")
    
    # Step 7: Verify file persistence
    print("\n[STEP 7] Verify data persisted to JSON file")
    json_file = DATA_DIR / f"{session_id}.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        print(f"✓ File saved at: {json_file}")
        print(f"✓ File contains {len(file_data['messages'])} messages")
        print(f"✓ Interest level in file: {file_data['analytics']['interest_level']}")
    
    print("\n" + "=" * 70)
    print("SUMMARY: Session Update Workflow Complete!")
    print("=" * 70)
    print("""
User can:
1. End session → Analytics extracted
2. Reopen session → Continue chatting OR
3. Update analytics directly → Manual corrections
4. All changes persisted to JSON file
5. Retrieve anytime via /session/{session_id}
    """)


if __name__ == "__main__":
    test_session_update_workflow()
