from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel


class BookingResult(BaseModel):
    ok: bool
    reason: str | None = None
    confirmation_id: str | None = None
    visit_date: str | None = None
    visit_time: str | None = None
    configuration: str | None = None


class SiteVisitCalendar:
    """In-memory bookings. Sundays and past dates fail so the agent can recover."""

    def __init__(self, today: date | None = None) -> None:
        self._today = today or date.today()
        self._bookings: list[BookingResult] = []

    def book(
        self,
        configuration: str,
        visit_date: str,
        visit_time: str,
    ) -> BookingResult:
        parsed = self._parse_date(visit_date)
        if parsed is None:
            return BookingResult(
                ok=False,
                reason="Please use a calendar date like 2026-08-24.",
            )
        if parsed < self._today:
            return BookingResult(
                ok=False,
                reason="That date is in the past. Please pick a future weekday.",
            )
        if parsed.weekday() == 6:
            return BookingResult(
                ok=False,
                reason="Sunday site visits are not available. Please pick Monday to Saturday.",
            )
        result = BookingResult(
            ok=True,
            confirmation_id=f"NS-{uuid4().hex[:8].upper()}",
            visit_date=visit_date,
            visit_time=visit_time,
            configuration=configuration,
        )
        self._bookings.append(result)
        return result

    def _parse_date(self, visit_date: str) -> date | None:
        try:
            return datetime.strptime(visit_date, "%Y-%m-%d").date()
        except ValueError:
            return None


calendar = SiteVisitCalendar()
