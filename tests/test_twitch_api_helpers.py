from services.twitch_api import TwitchApiService, TwitchSnapshot


def test_twitch_snapshot_to_dict():
    service = TwitchApiService("client", "dad_r3x", lambda: "token")

    snap = TwitchSnapshot(
        timestamp_epoch=123,
        stream_time="00:00:01",
        connected=True,
        live=True,
        channel_login="dad_r3x",
        viewer_count=3,
    )

    data = service.to_dict(snap)

    assert data["connected"] is True
    assert data["live"] is True
    assert data["viewer_count"] == 3
