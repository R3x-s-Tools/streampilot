from analytics.ai_throttle import AiTimelineThrottle


def test_ai_timeline_throttle_rules():
    throttle = AiTimelineThrottle(force_repeat_seconds=600)
    throttle.last_notes_text = "same"
    throttle.last_post_epoch = 1000

    assert throttle.should_post("", auto=True, now_epoch=1100) is False
    assert throttle.should_post("different", auto=True, now_epoch=1100) is True
    assert throttle.should_post("same", auto=True, now_epoch=1100) is False
    assert throttle.should_post("same", auto=False, now_epoch=1100) is True
    assert throttle.should_post("same", auto=True, now_epoch=1701) is True


def test_ai_timeline_throttle_mark_posted():
    throttle = AiTimelineThrottle(force_repeat_seconds=600)

    throttle.mark_posted("hello", now_epoch=1000)

    assert throttle.last_notes_text == "hello"
    assert throttle.last_post_epoch == 1000
    assert throttle.should_post("hello", auto=True, now_epoch=1200) is False
