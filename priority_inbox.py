"""
priority_inbox.py
-----------------
Stage 6 – Priority Inbox

Fetches notifications from the evaluation API, filters to unread only,
scores each notification by type weight and recency, then returns the
top N (default 10) most important notifications.

Priority rules:
  - Type weight  : placement=3  >  result=2  >  event=1
  - Recency boost: newer notifications rank higher within the same weight

Maintaining top-N efficiently as new notifications arrive:
  - On each explicit request, re-fetch and recompute (acceptable for this scale).
  - For high-volume production use, maintain a Redis Sorted Set keyed by
    priority score; insert new notifications with their score and query
    ZREVRANGE to get top-N in O(log N) without a full re-sort.

Usage:
    python priority_inbox.py                  # top 10 (default)
    python priority_inbox.py --top 15         # top 15
    python priority_inbox.py --top 20         # top 20
"""

import argparse
import datetime
import sys
from typing import Dict, List, Optional

import requests

from logging_utils import get_logger, log_execution_time

# ── Constants ─────────────────────────────────────────────────────────────────

API_URL = "http://4.224.186.213/evaluation-service/notifications"

TYPE_WEIGHTS: Dict[str, int] = {
    "placement": 3,
    "result": 2,
    "event": 1,
}

REQUEST_TIMEOUT_SECONDS = 10

# ── Logger ────────────────────────────────────────────────────────────────────

logger = get_logger("priority_inbox")

# ── Helpers ───────────────────────────────────────────────────────────────────


def get_type_weight(notification_type: str) -> int:
    """
    Return numeric weight for a notification type.
    Comparison is case-insensitive.
    Unknown types receive weight 0.
    """
    weight = TYPE_WEIGHTS.get(notification_type.lower().strip(), 0)
    logger.debug(
        "Resolved type weight",
        notification_type=notification_type,
        weight=weight,
    )
    return weight


def parse_created_at(created_at_str: str) -> Optional[datetime.datetime]:
    """
    Parse an ISO-8601 datetime string into a timezone-aware datetime.
    Returns None on failure.
    """
    if not created_at_str:
        return None
    try:
        # Python 3.7+: handles 'Z' suffix
        dt = datetime.datetime.fromisoformat(
            created_at_str.replace("Z", "+00:00")
        )
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except (ValueError, AttributeError) as exc:
        logger.warning(
            "Failed to parse createdAt",
            raw=created_at_str,
            error=str(exc),
        )
        return None


def compute_priority_score(notification: Dict) -> float:
    """
    Compute a composite priority score:

        score = type_weight * (1 + recency_factor)

    recency_factor is the notification's Unix timestamp normalised against
    the current time, so it is always in (0, 1].  This means a more recent
    notification beats an older one of the same type, while a placement
    always outranks a result regardless of age.

    Example:
        A placement from 1 hour ago  → 3 * (1 + ~0.9999) ≈ 5.9997
        A result    from 1 minute ago → 2 * (1 + ~1.0000) ≈ 4.0000
        → placement still wins.
    """
    type_weight = get_type_weight(
        notification.get("notificationType") or notification.get("type", "")
    )

    created_at_raw = (
        notification.get("createdAt")
        or notification.get("created_at")
        or ""
    )
    dt = parse_created_at(created_at_raw)

    if dt:
        now_ts = datetime.datetime.now(datetime.timezone.utc).timestamp()
        notif_ts = dt.timestamp()
        recency_factor = notif_ts / now_ts if now_ts > 0 else 0.0
    else:
        recency_factor = 0.0

    score = type_weight * (1 + recency_factor)
    logger.debug(
        "Computed priority score",
        notification_id=notification.get("id"),
        type_weight=type_weight,
        recency_factor=f"{recency_factor:.6f}",
        score=f"{score:.6f}",
    )
    return score


# ── Core functions ────────────────────────────────────────────────────────────


@log_execution_time(logger)
def fetch_notifications(api_url: str = API_URL) -> List[Dict]:
    """
    Fetch the full notification list from the evaluation API.
    Raises RuntimeError on non-200 responses.
    """
    logger.info("Fetching notifications from API", url=api_url)

    try:
        response = requests.get(api_url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection failed", url=api_url, error=str(exc))
        raise RuntimeError(f"Could not connect to {api_url}: {exc}") from exc
    except requests.exceptions.Timeout:
        logger.error("Request timed out", url=api_url, timeout=REQUEST_TIMEOUT_SECONDS)
        raise RuntimeError(f"Request to {api_url} timed out after {REQUEST_TIMEOUT_SECONDS}s")

    if response.status_code != 200:
        logger.error(
            "API returned non-200 status",
            status_code=response.status_code,
            url=api_url,
            body=response.text[:200],
        )
        raise RuntimeError(
            f"API request failed: HTTP {response.status_code}"
        )

    data = response.json()

    # API may return a list directly or wrap it in a key
    if isinstance(data, list):
        notifications = data
    elif isinstance(data, dict):
        notifications = (
            data.get("notifications")
            or data.get("items")
            or data.get("data")
            or []
        )
    else:
        notifications = []

    logger.info(
        "Successfully fetched notifications",
        total=len(notifications),
    )
    return notifications


@log_execution_time(logger)
def filter_unread(notifications: List[Dict]) -> List[Dict]:
    """
    Return only notifications where isRead / is_read is False.
    """
    logger.info("Filtering unread notifications", total_input=len(notifications))

    unread = [
        n for n in notifications
        if not (n.get("isRead") or n.get("is_read") or n.get("status") == "READ")
    ]

    logger.info(
        "Filtered unread notifications",
        unread_count=len(unread),
        read_count=len(notifications) - len(unread),
    )
    return unread


@log_execution_time(logger)
def rank_notifications(notifications: List[Dict]) -> List[Dict]:
    """
    Attach a _priority_score to each notification and sort
    descending so the most important notification is first.
    """
    logger.info("Computing priority scores", count=len(notifications))

    for n in notifications:
        n["_priority_score"] = compute_priority_score(n)

    ranked = sorted(notifications, key=lambda n: n["_priority_score"], reverse=True)
    logger.info("Ranking complete")
    return ranked


def get_top_n(notifications: List[Dict], n: int = 10) -> List[Dict]:
    """
    Full pipeline: fetch → filter unread → rank → return top N.
    """
    logger.info("Starting Priority Inbox pipeline", requested_top_n=n)

    all_notifications = fetch_notifications()
    unread = filter_unread(all_notifications)

    if not unread:
        logger.warning("No unread notifications found")
        return []

    ranked = rank_notifications(unread)
    top_n = ranked[:n]

    logger.info(
        "Priority Inbox pipeline complete",
        top_n_returned=len(top_n),
    )
    return top_n


# ── Display ───────────────────────────────────────────────────────────────────


def display_top_n(top_n: List[Dict]) -> None:
    """Pretty-print the top-N priority notifications to stdout."""
    separator = "─" * 72

    print(f"\n{'═' * 72}")
    print(f"  🔔  PRIORITY INBOX  —  Top {len(top_n)} Unread Notifications")
    print(f"{'═' * 72}\n")

    if not top_n:
        print("  No unread notifications found.\n")
        return

    for i, n in enumerate(top_n, start=1):
        notif_type = (
            n.get("notificationType") or n.get("type", "UNKNOWN")
        ).upper()
        title   = n.get("title", "—")
        message = n.get("message", "—")
        created = n.get("createdAt") or n.get("created_at") or "—"
        score   = n.get("_priority_score", 0.0)
        notif_id = n.get("id", "—")

        # Type badge
        badge_map = {"PLACEMENT": "🏢", "RESULT": "📊", "EVENT": "📅"}
        badge = badge_map.get(notif_type, "🔔")

        print(f"  #{i:02d}  {badge}  [{notif_type}]  {title}")
        print(f"        ID       : {notif_id}")
        print(f"        Message  : {message}")
        print(f"        Created  : {created}")
        print(f"        Score    : {score:.4f}")
        print(f"  {separator}")

    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Priority Inbox – top-N unread notifications by weight and recency"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top notifications to display (default: 10)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Priority Inbox starting", top_n=args.top)
    logger.info("=" * 60)

    try:
        top_n = get_top_n(n=args.top)
    except RuntimeError as exc:
        logger.critical("Pipeline failed", error=str(exc))
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)

    display_top_n(top_n)

    # Log summary
    logger.info("Summary of top notifications:")
    for i, n in enumerate(top_n, start=1):
        logger.info(
            f"  Rank #{i}",
            id=n.get("id"),
            type=n.get("notificationType") or n.get("type"),
            title=n.get("title"),
            score=f"{n.get('_priority_score', 0):.4f}",
            createdAt=n.get("createdAt") or n.get("created_at"),
        )


if __name__ == "__main__":
    main()
