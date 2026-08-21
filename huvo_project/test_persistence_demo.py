#!/usr/bin/env python3
"""
Demo script showing JSON persistence of user sessions using session_id.
Run this to see how session data is saved.
"""
import json
from pathlib import Path
from app.memory import SessionStore
from app.config import DATA_DIR


def demo_session_persistence():
    """Demonstrate saving user info to JSON file using session ID."""
    store = SessionStore()
    
    # Simulate a conversation
    session_id = "demo-session-123"
    
    # Add some messages
    store.append(session_id, {"role": "user", "content": "2 BHK dekhna hai"})
    store.append(session_id, {"role": "assistant", "content": "2 BHK 1.35 crore se start hai"})
    store.append(session_id, {"role": "user", "content": "Book a site visit"})
    store.append(session_id, {"role": "assistant", "content": "Site visit booked!"})
    
    # Mark conversation as ended
    store.mark_ended(session_id)
    
    # Simulate analytics extraction
    user_analytics = {
        "language": "hinglish",
        "configuration": "2bhk",
        "budget": "1.35 crore",
        "interest_level": "hot",
        "site_visit_status": "booked",
        "follow_up_required": False,
        "objections": [],
        "outcome": "booked",
        "opted_out": False,
        "escalated": False,
        "callback_time": None,
        "notes": "Customer booked site visit for 2 BHK property"
    }
    
    # Save user info to JSON file
    store.set_analytics(session_id, user_analytics)
    
    # Verify file was created
    json_file = DATA_DIR / f"{session_id}.json"
    if json_file.exists():
        print(f"✓ Session saved to: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        print(f"\n✓ Saved data:")
        print(json.dumps(saved_data, indent=2, ensure_ascii=False))
        return True
    else:
        print(f"✗ Failed to save session to {json_file}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: User Session Persistence using Session ID")
    print("=" * 60)
    success = demo_session_persistence()
    if success:
        print("\n" + "=" * 60)
        print("✓ SUCCESS: User data persisted to JSON!")
        print("=" * 60)
    else:
        print("\n✗ FAILED")
