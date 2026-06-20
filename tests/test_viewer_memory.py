from analytics.viewer_memory import ViewerMemory


def test_viewer_memory_tracks_new_human_viewer(tmp_path):
    memory = ViewerMemory(path=str(tmp_path / "viewer_memory.json"))

    result = memory.observe_chat("Fythern", "I love Squad and FiveM", 1000)

    assert result["ignored"] is False
    assert result["is_new_viewer"] is True
    assert result["total_messages"] == 1
    assert "squad" in result["topics"]
    assert "gta_rp" in result["topics"]


def test_viewer_memory_ignores_bots(tmp_path):
    memory = ViewerMemory(path=str(tmp_path / "viewer_memory.json"))

    result = memory.observe_chat("stream_pops", "Automated message", 1000)

    assert result["ignored"] is True
