from datetime import datetime, timezone


def validate_tle_structure(line1, line2):
    """Check basic TLE structure and matching NORAD IDs."""

    if not line1.startswith("1 "):
        return False, "Invalid TLE line 1"

    if not line2.startswith("2 "):
        return False, "Invalid TLE line 2"

    if len(line1) < 69 or len(line2) < 69:
        return False, "TLE line is too short"

    norad_1 = line1[2:7].strip()
    norad_2 = line2[2:7].strip()

    if not norad_1 or not norad_2:
        return False, "Missing NORAD ID"

    if norad_1 != norad_2:
        return False, "TLE lines belong to different objects"

    return True, "Structure valid"


def calculate_checksum(line):
    """Calculate the TLE checksum for a single line."""

    checksum = 0

    for character in line[:68]:
        if character.isdigit():
            checksum += int(character)
        elif character == "-":
            checksum += 1

    return checksum % 10


def validate_checksum(line):
    """Validate the checksum digit at the end of a TLE line."""

    if len(line) < 69:
        return False, "TLE line is too short"

    if not line[68].isdigit():
        return False, "Missing checksum digit"

    expected = calculate_checksum(line)
    actual = int(line[68])

    if expected != actual:
        return False, "Invalid checksum"

    return True, "Checksum valid"


def validate_epoch(line1):
    """Validate the epoch field contained in TLE line 1."""

    try:
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])

        year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year

        datetime(year, 1, 1, tzinfo=timezone.utc)

        if epoch_day < 1 or epoch_day >= 367:
            return False, "Invalid epoch day"

    except (ValueError, IndexError):
        return False, "Invalid epoch format"

    return True, "Epoch valid"


def validate_tle_pair(line1, line2):
    """Run all validation checks on a TLE pair."""

    checks = [
        validate_tle_structure(line1, line2),
        validate_checksum(line1),
        validate_checksum(line2),
        validate_epoch(line1),
    ]

    for is_valid, message in checks:
        if not is_valid:
            return False, message

    return True, "TLE pair valid"