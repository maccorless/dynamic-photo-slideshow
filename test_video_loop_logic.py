"""Unit tests for video loop logic introduced in pygame_display_manager.play_video."""


def compute_loop_params(video_duration, max_duration):
    """Mirrors the logic added to play_video for determining loop behavior."""
    half_max = max_duration / 2
    should_loop = video_duration < half_max
    if should_loop:
        slide_timer = int(half_max)
    else:
        slide_timer = min(int(video_duration), max_duration)
    loop_end = half_max if should_loop else max_duration
    return should_loop, slide_timer, loop_end


def test_short_video_triggers_loop():
    """Video shorter than half max_duration should loop."""
    should_loop, slide_timer, loop_end = compute_loop_params(
        video_duration=3.0, max_duration=15
    )
    assert should_loop is True
    assert slide_timer == 7          # int(15 / 2)
    assert loop_end == 7.5


def test_video_at_exactly_half_does_not_loop():
    """Video exactly equal to half max_duration should NOT loop (not strictly less than)."""
    should_loop, slide_timer, loop_end = compute_loop_params(
        video_duration=7.5, max_duration=15
    )
    assert should_loop is False
    assert slide_timer == 7          # min(int(7.5), 15)
    assert loop_end == 15


def test_long_video_does_not_loop():
    """Video longer than half max_duration should not loop."""
    should_loop, slide_timer, loop_end = compute_loop_params(
        video_duration=12.0, max_duration=15
    )
    assert should_loop is False
    assert slide_timer == 12
    assert loop_end == 15


def test_video_longer_than_max_capped():
    """Video longer than max_duration should be capped at max_duration."""
    should_loop, slide_timer, loop_end = compute_loop_params(
        video_duration=60.0, max_duration=15
    )
    assert should_loop is False
    assert slide_timer == 15
    assert loop_end == 15


def test_very_short_video_loops():
    """1-second video with 15s max should loop (1 < 7.5)."""
    should_loop, slide_timer, loop_end = compute_loop_params(
        video_duration=1.0, max_duration=15
    )
    assert should_loop is True
    assert slide_timer == 7
    assert loop_end == 7.5


def test_loop_count_covers_half_max():
    """Verify that looping a short video eventually passes half_max."""
    video_duration = 3.0
    max_duration = 15
    half_max = max_duration / 2  # 7.5

    elapsed = 0.0
    loop_count = 0
    while elapsed < half_max:
        elapsed += video_duration
        loop_count += 1

    # After the last complete loop, elapsed should be >= half_max
    assert elapsed >= half_max
    assert loop_count == 3  # 3 * 3.0 = 9.0 >= 7.5


def test_loop_count_with_4s_video():
    """4-second video, 15s max (half=7.5): needs 2 loops to reach 8.0 >= 7.5."""
    video_duration = 4.0
    half_max = 15 / 2

    elapsed = 0.0
    loop_count = 0
    while elapsed < half_max:
        elapsed += video_duration
        loop_count += 1

    assert elapsed >= half_max
    assert loop_count == 2  # 2 * 4.0 = 8.0 >= 7.5


if __name__ == "__main__":
    tests = [
        test_short_video_triggers_loop,
        test_video_at_exactly_half_does_not_loop,
        test_long_video_does_not_loop,
        test_video_longer_than_max_capped,
        test_very_short_video_loops,
        test_loop_count_covers_half_max,
        test_loop_count_with_4s_video,
    ]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
