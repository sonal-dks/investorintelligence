"""Dashboard endpoints."""

from fastapi import APIRouter, Depends

from backend.config import Settings, get_settings
from backend.deps import get_current_user_id
from backend.models.schemas import (
    BookingSummaryResponse,
    DashboardOverviewResponse,
    FundStripResponse,
    KPIResponse,
    PulsePreviewResponse,
)
from backend.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_dashboard_service(settings: Settings = Depends(get_settings)) -> DashboardService:
    return DashboardService(settings)


@router.get("/kpis", response_model=KPIResponse)
def get_kpis(
    user_id: str = Depends(get_current_user_id),
    svc: DashboardService = Depends(get_dashboard_service),
) -> KPIResponse:
    return svc.get_kpis(user_id)


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_overview(
    user_id: str = Depends(get_current_user_id),
    svc: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverviewResponse:
    return svc.get_overview(user_id)


@router.get("/bookings", response_model=BookingSummaryResponse)
def get_bookings(
    user_id: str = Depends(get_current_user_id),
    svc: DashboardService = Depends(get_dashboard_service),
) -> BookingSummaryResponse:
    return svc.get_booking_summary(user_id)


@router.get("/fund-strip", response_model=FundStripResponse)
def get_fund_strip(svc: DashboardService = Depends(get_dashboard_service)) -> FundStripResponse:
    return svc.get_fund_strip()


@router.get("/pulse-preview", response_model=PulsePreviewResponse)
def get_pulse_preview(svc: DashboardService = Depends(get_dashboard_service)) -> PulsePreviewResponse:
    return svc.get_pulse_preview()
