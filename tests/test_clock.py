from forms_library.clock import CINCINNATI_TIMEZONE, current_date, current_datetime


def test_current_datetime_uses_cincinnati_timezone():
    timestamp = current_datetime()

    assert timestamp.tzinfo == CINCINNATI_TIMEZONE
    assert current_date() == timestamp.date()
