"""Validates scraped fund and review data against schemas before insert."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from backend.models.schemas import FundData, ReviewData, ValidationError

logger = logging.getLogger(__name__)


def validate_funds(funds: list[dict[str, Any]]) -> tuple[list[FundData], list[ValidationError]]:
    """Split raw fund dicts into valid FundData objects and validation errors."""
    valid: list[FundData] = []
    errors: list[ValidationError] = []

    for i, raw in enumerate(funds):
        try:
            fund = FundData(**raw)
            valid.append(fund)
        except PydanticValidationError as e:
            for err in e.errors():
                errors.append(
                    ValidationError(
                        index=i,
                        field=".".join(str(loc) for loc in err["loc"]),
                        message=err["msg"],
                        raw_data=raw,
                    )
                )
            logger.warning("Fund validation failed at index %d: %s", i, e.error_count())

    logger.info("Fund validation: %d valid, %d errors", len(valid), len(errors))
    return valid, errors


def validate_reviews(reviews: list[dict[str, Any]]) -> tuple[list[ReviewData], list[ValidationError]]:
    """Split raw review dicts into valid ReviewData objects and validation errors."""
    valid: list[ReviewData] = []
    errors: list[ValidationError] = []

    for i, raw in enumerate(reviews):
        try:
            review = ReviewData(**raw)
            valid.append(review)
        except PydanticValidationError as e:
            for err in e.errors():
                errors.append(
                    ValidationError(
                        index=i,
                        field=".".join(str(loc) for loc in err["loc"]),
                        message=err["msg"],
                        raw_data=raw,
                    )
                )
            logger.warning("Review validation failed at index %d: %s", i, e.error_count())

    logger.info("Review validation: %d valid, %d errors", len(valid), len(errors))
    return valid, errors
