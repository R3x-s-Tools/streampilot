from analytics.conversation_engine import ConversationEngine


def test_conversation_engine_detects_high_engagement_user():
    engine = ConversationEngine()
    chat = [
        {"timestamp_epoch": 1000, "username": "fythern", "message": "I play Squad"},
        {"timestamp_epoch": 1010, "username": "fythern", "message": "What kit do you like?"},
        {"timestamp_epoch": 1020, "username": "fythern", "message": "Map is important"},
        {"timestamp_epoch": 1030, "username": "fythern", "message": "FOB placement matters"},
    ]

    signals = engine.analyze_recent_chat(chat, now_epoch=1040)

    assert len(signals) == 1
    assert signals[0]["username"] == "fythern"
    assert signals[0]["is_high_engagement"] is True
    assert "Squad" in signals[0]["suggested_prompt"]
