def unixConvert(seconds: float) -> list[int, int, int]:
    remaining_minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)
    hours = int(seconds // 3600)

    return [remaining_seconds, remaining_minutes, hours]