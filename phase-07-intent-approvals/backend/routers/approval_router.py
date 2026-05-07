from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from backend.models.schemas import (
    ApprovalListResponse,
    ApprovalPatchRequest,
    ApprovalStatsResponse,
    DetectIntentsRequest,
    DetectIntentsResponse,
)
from backend.services.approval_generator_service import ApprovalGeneratorService
from backend.services.approval_service import ApprovalService
from backend.services.intent_detection_service import IntentDetectionService
from backend.services.intent_tracker import IntentTracker

router = APIRouter(prefix='/api', tags=['phase-07-approvals'])

detector = IntentDetectionService()
tracker = IntentTracker()
generator = ApprovalGeneratorService()
approvals = ApprovalService()


@router.post('/intents/detect', response_model=DetectIntentsResponse)
def detect_intents(req: DetectIntentsRequest) -> DetectIntentsResponse:
    intents = detector.detect(req.messages)
    tracked, transitions = tracker.track(req.session_id, intents)

    for transition in transitions:
        current = next((i for i in tracked if tracker.compute_hash(req.session_id, i.type, i.details) == transition.intent_hash), None)
        if current is None:
            continue

        if current.confidence < 0.7:
            continue

        if transition.to_status in ('confirmed', 'modified'):
            approval = generator.create(
                session_id=req.session_id,
                investor_id='investor-demo',
                investor_name='Demo Investor',
                intent=current,
            )
            approvals.upsert_pending(approval)
        if transition.to_status == 'cancelled':
            approvals.cancel_by_intent_hash(req.session_id, transition.intent_hash)

    return DetectIntentsResponse(intents=tracked)


@router.get('/approvals', response_model=ApprovalListResponse)
def list_approvals(
    status: str = Query('all', pattern='^(all|pending|approved|rejected)$'),
    user_id: str | None = Query(default=None),
) -> ApprovalListResponse:
    items = approvals.list(status=status, user_id=user_id)
    stats = approvals.stats()
    return ApprovalListResponse(items=items, total=len(items), pending_count=stats['pending'])


@router.get('/approvals/{approval_id}')
def get_approval(approval_id: str):
    item = approvals.get(approval_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Approval not found')
    return item


@router.patch('/approvals/{approval_id}')
def patch_approval(
    approval_id: str,
    body: ApprovalPatchRequest,
    x_user_role: str = Header(default='investor'),
):
    if x_user_role.lower() != 'admin':
        raise HTTPException(status_code=403, detail='Only admin can review approvals')
    item = approvals.patch(approval_id, status=body.status, reviewed_by=body.reviewed_by)
    if item is None:
        raise HTTPException(status_code=404, detail='Approval not found')
    return item


@router.get('/approvals/stats', response_model=ApprovalStatsResponse)
def approval_stats() -> ApprovalStatsResponse:
    stats = approvals.stats()
    return ApprovalStatsResponse(**stats)
