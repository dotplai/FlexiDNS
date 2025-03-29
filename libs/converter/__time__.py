def unixConvert(seconds: float) -> tuple[int, int, int, int]:
    milliseconds = seconds * 1000
    remaining_minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60
    hours = int(seconds // 3600)

    return milliseconds, remaining_seconds, remaining_minutes, hours