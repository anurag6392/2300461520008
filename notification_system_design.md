# Stage 1

## Notification Platform – REST API Design & Contract

### Core Actions Supported

The notification platform supports the following core actions:

1. **Fetch notifications** – retrieve all notifications for the logged-in user
2. **Fetch a single notification** – get details of a specific notification
3. **Mark notification(s) as read** – update read status
4. **Delete a notification** – remove a notification
5. **Mark all as read** – bulk update
6. **Get unread count** – badge/count for UI indicator
7. **Subscribe to real-time notifications** – SSE or WebSocket endpoint

---

### Base URL

```
https://api.example.com/v1
```

All endpoints require the `Authorization` header with a valid Bearer token (JWT).

---

### Common Headers

#### Request Headers

```json
{
  "Authorization": "Bearer <jwt_token>",
  "Content-Type": "application/json",
  "Accept": "application/json",
  "X-Request-ID": "uuid-v4-string"
}
```

#### Response Headers

```json
{
  "Content-Type": "application/json",
  "X-Request-ID": "uuid-v4-string",
  "X-RateLimit-Limit": "100",
  "X-RateLimit-Remaining": "95",
  "X-RateLimit-Reset": "1718097600"
}
```

---

### Endpoints

---

#### 1. GET `/notifications`

**Description:** Retrieve a paginated list of notifications for the authenticated user.

**Query Parameters:**

| Parameter  | Type    | Required | Description                              |
|------------|---------|----------|------------------------------------------|
| `page`     | integer | No       | Page number (default: 1)                 |
| `limit`    | integer | No       | Results per page (default: 20, max: 100) |
| `is_read`  | boolean | No       | Filter by read/unread status             |
| `type`     | string  | No       | Filter by notification type              |

**Request:**

```
GET /notifications?page=1&limit=20&is_read=false
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_01HZ9K2X3P",
        "user_id": "user_abc123",
        "type": "appointment_reminder",
        "title": "Upcoming Appointment",
        "message": "You have an appointment scheduled for tomorrow at 10:00 AM.",
        "is_read": false,
        "metadata": {
          "appointment_id": "appt_789",
          "doctor_name": "Dr. Sharma"
        },
        "created_at": "2026-06-10T08:30:00Z",
        "updated_at": "2026-06-10T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

#### 2. GET `/notifications/:id`

**Description:** Retrieve a single notification by its ID.

**Path Parameters:**

| Parameter | Type   | Required | Description         |
|-----------|--------|----------|---------------------|
| `id`      | string | Yes      | Notification ID     |

**Request:**

```
GET /notifications/notif_01HZ9K2X3P
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "data": {
    "id": "notif_01HZ9K2X3P",
    "user_id": "user_abc123",
    "type": "appointment_reminder",
    "title": "Upcoming Appointment",
    "message": "You have an appointment scheduled for tomorrow at 10:00 AM.",
    "is_read": false,
    "metadata": {
      "appointment_id": "appt_789",
      "doctor_name": "Dr. Sharma"
    },
    "created_at": "2026-06-10T08:30:00Z",
    "updated_at": "2026-06-10T08:30:00Z"
  }
}
```

**Response: 404 Not Found**

```json
{
  "success": false,
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Notification with the given ID does not exist."
  }
}
```

---

#### 3. PATCH `/notifications/:id/read`

**Description:** Mark a specific notification as read.

**Path Parameters:**

| Parameter | Type   | Required | Description     |
|-----------|--------|----------|-----------------|
| `id`      | string | Yes      | Notification ID |

**Request:**

```
PATCH /notifications/notif_01HZ9K2X3P/read
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "data": {
    "id": "notif_01HZ9K2X3P",
    "is_read": true,
    "updated_at": "2026-06-11T09:00:00Z"
  }
}
```

---

#### 4. PATCH `/notifications/read-all`

**Description:** Mark all unread notifications as read for the authenticated user.

**Request:**

```
PATCH /notifications/read-all
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "data": {
    "updated_count": 12
  }
}
```

---

#### 5. DELETE `/notifications/:id`

**Description:** Delete a specific notification.

**Path Parameters:**

| Parameter | Type   | Required | Description     |
|-----------|--------|----------|-----------------|
| `id`      | string | Yes      | Notification ID |

**Request:**

```
DELETE /notifications/notif_01HZ9K2X3P
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "message": "Notification deleted successfully."
}
```

---

#### 6. GET `/notifications/unread-count`

**Description:** Get the count of unread notifications for the authenticated user (used for UI badge).

**Request:**

```
GET /notifications/unread-count
Authorization: Bearer <jwt_token>
```

**Response: 200 OK**

```json
{
  "success": true,
  "data": {
    "unread_count": 7
  }
}
```

---

### Notification Object Schema

```json
{
  "id": "string (unique identifier, prefixed: notif_)",
  "user_id": "string (reference to the authenticated user)",
  "type": "string (enum: appointment_reminder | lab_result | prescription_update | system_alert | message | billing)",
  "title": "string (short, human-readable title)",
  "message": "string (full notification body)",
  "is_read": "boolean (default: false)",
  "metadata": "object (optional, type-specific additional data)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

---

### Error Response Schema

All error responses follow a consistent structure:

```json
{
  "success": false,
  "error": {
    "code": "string (machine-readable error code)",
    "message": "string (human-readable description)",
    "details": "object (optional, validation errors or extra context)"
  }
}
```

**Common HTTP Error Codes:**

| Status | Code                    | Description                          |
|--------|-------------------------|--------------------------------------|
| 400    | `INVALID_REQUEST`       | Malformed request or bad parameters  |
| 401    | `UNAUTHORIZED`          | Missing or invalid JWT token         |
| 403    | `FORBIDDEN`             | Action not permitted for this user   |
| 404    | `NOTIFICATION_NOT_FOUND`| Resource does not exist              |
| 429    | `RATE_LIMIT_EXCEEDED`   | Too many requests                    |
| 500    | `INTERNAL_SERVER_ERROR` | Unexpected server error              |

---

### Real-Time Notification Mechanism

#### Approach: Server-Sent Events (SSE)

SSE is recommended over WebSockets for one-way server-to-client notification delivery. It is simpler to implement, works over standard HTTP/2, supports automatic reconnection natively in browsers, and is well-suited for read-only push events.

**Endpoint:** `GET /notifications/stream`

```
GET /notifications/stream
Authorization: Bearer <jwt_token>
Accept: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Response: 200 OK (persistent stream)**

```
Content-Type: text/event-stream
X-Accel-Buffering: no

event: notification
data: {"id":"notif_01HZ9K2X3P","type":"appointment_reminder","title":"Upcoming Appointment","message":"You have an appointment tomorrow at 10:00 AM.","is_read":false,"created_at":"2026-06-11T09:15:00Z"}

event: ping
data: {"timestamp":"2026-06-11T09:15:30Z"}
```

**SSE Event Types:**

| Event          | Description                                              |
|----------------|----------------------------------------------------------|
| `notification` | A new notification has been created for the user         |
| `read`         | A notification has been marked as read (sync across tabs)|
| `delete`       | A notification has been deleted                          |
| `ping`         | Heartbeat sent every 30 seconds to keep connection alive |

**Client Reconnection:** Browsers automatically reconnect using the `Last-Event-ID` header. The server should replay missed events since that ID.

**Fallback:** For environments not supporting SSE, clients can poll `GET /notifications?is_read=false` every 30–60 seconds.

---

---

# Stage 2

## Persistent Storage – DB Design, Schema, Scalability & Queries

### Recommended Database: PostgreSQL

**Rationale:**

PostgreSQL is the recommended choice for the notification platform due to the following reasons:

- **Structured, relational data**: Notifications have a well-defined schema with a clear relationship to users, making a relational model a natural fit.
- **JSONB support**: The `metadata` field is flexible and type-specific. PostgreSQL's `JSONB` type supports efficient indexing and querying of semi-structured data without sacrificing relational integrity.
- **ACID compliance**: Guarantees consistency for operations like marking all notifications as read.
- **Scalability features**: Supports table partitioning, partial indexes, and connection pooling (via PgBouncer), which address the high-volume challenges described below.
- **Mature ecosystem**: Well-supported with ORMs, migration tools, and monitoring integrations.

A NoSQL alternative like **MongoDB** would be a valid choice if the schema were highly variable or the team prioritised horizontal write scaling from day one, but for a notification service with a predictable schema, PostgreSQL's query power and consistency guarantees are the better tradeoff.

---

### DB Schema

```sql
-- Users table (referenced; assumed to exist in the wider system)
CREATE TABLE users (
    id          VARCHAR(64) PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Notification types enum
CREATE TYPE notification_type AS ENUM (
    'appointment_reminder',
    'lab_result',
    'prescription_update',
    'system_alert',
    'message',
    'billing'
);

-- Core notifications table
CREATE TABLE notifications (
    id          VARCHAR(64)       PRIMARY KEY,              -- e.g. notif_01HZ9K2X3P
    user_id     VARCHAR(64)       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        notification_type NOT NULL,
    title       VARCHAR(255)      NOT NULL,
    message     TEXT              NOT NULL,
    is_read     BOOLEAN           NOT NULL DEFAULT FALSE,
    metadata    JSONB,                                       -- flexible, type-specific payload
    created_at  TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

-- Index: fetch all notifications for a user (most common query)
CREATE INDEX idx_notifications_user_id
    ON notifications (user_id, created_at DESC);

-- Index: fetch unread notifications for a user (badge count + filtered list)
CREATE INDEX idx_notifications_unread
    ON notifications (user_id, is_read)
    WHERE is_read = FALSE;                                   -- partial index

-- Index: filter by type per user
CREATE INDEX idx_notifications_user_type
    ON notifications (user_id, type);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### Scalability Problems & Solutions

As data volume grows (millions of notifications across hundreds of thousands of users), the following problems emerge:

#### Problem 1: Table size and slow full-table scans

**Issue:** A single `notifications` table with 100M+ rows makes even indexed queries slower due to index bloat and vacuum overhead.

**Solution – Range Partitioning by `created_at`:**

```sql
-- Re-create as partitioned table (applied at schema design time)
CREATE TABLE notifications (
    id         VARCHAR(64)       NOT NULL,
    user_id    VARCHAR(64)       NOT NULL,
    type       notification_type NOT NULL,
    title      VARCHAR(255)      NOT NULL,
    message    TEXT              NOT NULL,
    is_read    BOOLEAN           NOT NULL DEFAULT FALSE,
    metadata   JSONB,
    created_at TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ       NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE notifications_2026_06
    PARTITION OF notifications
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE notifications_2026_07
    PARTITION OF notifications
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
-- etc.
```

Old partitions can be detached and archived (e.g., to S3 via `pg_partman`), keeping the active table small.

---

#### Problem 2: Unread count query becomes expensive

**Issue:** `SELECT COUNT(*) WHERE user_id = ? AND is_read = FALSE` on a large table is slow even with an index when many users query simultaneously.

**Solution – Denormalized counter table:**

```sql
CREATE TABLE notification_counts (
    user_id      VARCHAR(64) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    unread_count INTEGER NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Increment on insert of unread notification
-- Decrement on mark-as-read
-- Managed via application logic or DB triggers
```

The `GET /notifications/unread-count` endpoint then reads from this O(1) lookup table instead of aggregating the main table.

---

#### Problem 3: Write throughput at scale

**Issue:** High-frequency notification inserts (e.g., system-wide alerts sent to all users) can overwhelm synchronous writes.

**Solution – Async write queue:**

Use a message queue (e.g., Redis Streams, RabbitMQ, or Kafka) to buffer notification creation events. A worker pool consumes the queue and performs batched inserts into PostgreSQL. This decouples the API response time from DB write latency.

---

#### Problem 4: Old notifications accumulate indefinitely

**Solution – TTL-based archival policy:**

Automatically move or delete notifications older than a defined threshold (e.g., 90 days for read notifications) using a scheduled job or partition detachment.

---

### SQL Queries Based on Stage 1 APIs

#### `GET /notifications` – Paginated list for a user

```sql
SELECT
    id,
    user_id,
    type,
    title,
    message,
    is_read,
    metadata,
    created_at,
    updated_at
FROM notifications
WHERE user_id = $1
  AND ($2::boolean IS NULL OR is_read = $2)   -- optional is_read filter
  AND ($3::notification_type IS NULL OR type = $3) -- optional type filter
ORDER BY created_at DESC
LIMIT $4 OFFSET $5;                             -- $4 = limit, $5 = (page-1)*limit

-- Count query for pagination metadata
SELECT COUNT(*)
FROM notifications
WHERE user_id = $1
  AND ($2::boolean IS NULL OR is_read = $2);
```

---

#### `GET /notifications/:id` – Fetch single notification

```sql
SELECT
    id,
    user_id,
    type,
    title,
    message,
    is_read,
    metadata,
    created_at,
    updated_at
FROM notifications
WHERE id = $1
  AND user_id = $2;   -- enforce ownership
```

---

#### `PATCH /notifications/:id/read` – Mark one as read

```sql
UPDATE notifications
SET is_read = TRUE
WHERE id = $1
  AND user_id = $2
  AND is_read = FALSE   -- no-op guard
RETURNING id, is_read, updated_at;

-- Decrement counter
UPDATE notification_counts
SET unread_count = GREATEST(unread_count - 1, 0),
    updated_at   = NOW()
WHERE user_id = $2;
```

---

#### `PATCH /notifications/read-all` – Mark all as read

```sql
WITH updated AS (
    UPDATE notifications
    SET is_read = TRUE
    WHERE user_id = $1
      AND is_read = FALSE
    RETURNING id
)
SELECT COUNT(*) AS updated_count FROM updated;

-- Reset counter
UPDATE notification_counts
SET unread_count = 0,
    updated_at   = NOW()
WHERE user_id = $1;
```

---

#### `DELETE /notifications/:id` – Delete a notification

```sql
DELETE FROM notifications
WHERE id = $1
  AND user_id = $2;

-- If it was unread, decrement counter
UPDATE notification_counts
SET unread_count = GREATEST(unread_count - 1, 0),
    updated_at   = NOW()
WHERE user_id = $2
  AND EXISTS (
      SELECT 1 FROM notifications
      WHERE id = $1 AND is_read = FALSE
  );
```

---

#### `GET /notifications/unread-count` – Unread badge count

```sql
-- Fast path: denormalized counter
SELECT unread_count
FROM notification_counts
WHERE user_id = $1;

-- Fallback (if counter table not yet populated):
SELECT COUNT(*) AS unread_count
FROM notifications
WHERE user_id = $1
  AND is_read = FALSE;
```

---

#### Insert new notification (internal service / worker)

```sql
INSERT INTO notifications (id, user_id, type, title, message, metadata)
VALUES ($1, $2, $3, $4, $5, $6::jsonb)
RETURNING *;

-- Increment unread counter (upsert)
INSERT INTO notification_counts (user_id, unread_count)
VALUES ($2, 1)
ON CONFLICT (user_id)
DO UPDATE SET
    unread_count = notification_counts.unread_count + 1,
    updated_at   = NOW();
```

---

# Stage 3

## Query Optimization and Indexing

An earlier developer chose a relational database (MySQL / PostgreSQL) 3 months ago. The database has grown to **50,000 students** and **5,000,000 notifications**. The following query is now performing slowly:

```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt ASC;
```

### Is this query logically accurate?

Yes. It correctly filters by `studentID` and `isRead = false`, and orders by `createdAt` ascending. The logic is sound, but the implementation has serious performance problems at scale.

### Why is it slow?

1. **`SELECT *`** fetches every column, increasing I/O and memory usage even when only a few fields are needed by the UI.
2. **No composite index** on `(studentID, isRead, createdAt)` forces a full table scan or large range scan over 5,000,000 rows.
3. **`ORDER BY createdAt`** without an index-supported sort requires PostgreSQL/MySQL to sort the filtered result set in memory — an expensive extra step.
4. **No `LIMIT`** means the query can return thousands of rows in one shot, overwhelming both the DB and the application layer.

### Improved query

```sql
SELECT
  id,
  studentID,
  isRead,
  createdAt,
  notificationType,
  title,
  message
FROM notifications
WHERE studentID = 1042
  AND isRead = false
ORDER BY createdAt ASC
LIMIT 100;
```

**Changes made:**
- Select only the columns the application actually needs instead of `SELECT *`.
- Add `LIMIT 100` so the backend paginates results rather than fetching everything at once.
- Both changes reduce I/O, memory pressure, and network transfer.

### Indexing strategy

Add a single **composite index** that covers the filter columns and the sort column:

```sql
CREATE INDEX idx_notifications_student_unread_created
  ON notifications (studentID, isRead, createdAt);
```

This index allows the database to:
- Seek directly to rows for `studentID = 1042`.
- Filter `isRead = false` within that seek.
- Return rows already ordered by `createdAt` — no extra sort step.

**Why not index every column?**

Adding an index on every column is counter-productive:
- Every `INSERT` and `UPDATE` must maintain all indexes, increasing write latency.
- Indexes consume significant disk space.
- The query planner may choose a suboptimal index if too many exist.
- Indexes only help queries whose `WHERE` and `ORDER BY` clauses align with the index column order.

The composite index above is sufficient for all read-heavy queries in this platform.

### Query: students who received a placement notification in the last 7 days

```sql
-- PostgreSQL
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL '7 days';

-- MySQL
SELECT DISTINCT studentID
FROM notifications
WHERE notificationType = 'Placement'
  AND createdAt >= NOW() - INTERVAL 7 DAY;
```

This query benefits from a composite index on `(notificationType, createdAt)` or the broader index extended to include `notificationType`.

---

# Stage 4

## Performance Caching and Strategies

**Problem:** Notifications are fetched on every page load for every student, overwhelming the database and causing a poor user experience.

### Solution 1 — Redis Caching (Recommended)

Cache both the unread count and recent notifications per student in Redis.

**Cache keys:**
- `unread_count:{studentID}` → integer
- `notifications:{studentID}:{page}:{pageSize}` → JSON array

**Flow:**
1. On page load, check Redis for the student's data.
2. If cache hit → return immediately (sub-millisecond).
3. If cache miss → query the DB, populate the cache, return.

**Cache invalidation:**
- A new notification is created → increment `unread_count:{studentID}`, delete the page caches for that student.
- A notification is marked as read → decrement `unread_count:{studentID}`, delete affected page caches.
- A notification is deleted → same as mark-as-read invalidation.

**TTL:** 5–10 minutes as a safety net, even with event-driven invalidation.

| Pros | Cons |
|------|------|
| Dramatically reduces DB load | Requires Redis infrastructure |
| Sub-millisecond reads for cached data | Cache invalidation logic adds complexity |
| Handles high concurrent traffic well | Stale data possible if invalidation is missed |

### Solution 2 — Database Query Optimization and Pagination

Use the composite index from Stage 3, enforce `LIMIT`/`OFFSET` pagination, and eliminate `SELECT *`.

| Pros | Cons |
|------|------|
| No extra infrastructure needed | Still hits DB on every request |
| Simple to implement | Not sufficient alone for very high traffic |

### Solution 3 — Asynchronous Background Workers

Use background workers (Node.js workers, Python Celery, BullMQ, etc.) to:
- Pre-compute and warm the cache for active students.
- Handle bulk operations such as `notify_all` without blocking API responses.

| Pros | Cons |
|------|------|
| Keeps API response times low | Adds message queue infrastructure |
| Best for bulk/batch operations | Failure handling and retries add complexity |

### Recommended Combined Strategy

1. **Add the composite index** (Stage 3) — zero infrastructure cost, immediate improvement.
2. **Cache unread counts and recent notifications in Redis** — biggest single impact on DB load.
3. **Use background workers for `notify_all`** — keeps bulk sends from blocking real-time requests.

This layered approach gives the best balance of performance, reliability, and implementation effort.

---

# Stage 5

## Reliable and Fast `notify_all`

### Original pseudocode

```python
function notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)   # calls Email API
        save_to_db(student_id, message)   # DB insert
        push_to_app(student_id, message)  # real-time notification
```

### Shortcomings

1. **No error handling** — if `send_email` fails for any student, the loop continues silently and those students never receive the email.
2. **No logging** — there is no record of which students succeeded or failed.
3. **No retries** — transient failures (network blip, rate-limit) are permanent.
4. **Sequential processing** — iterating one-by-one over 50,000 students is extremely slow.
5. **Coupled concerns** — DB save and external API call are in the same synchronous step; a failure in one affects the other with no recovery path.
6. **Not scalable** — unsuitable for large-scale batch notifications.

### What happens if `send_email` fails for 200 students midway?

Those 200 students silently miss the email. There is no failure record, no retry, and no way to identify which students were affected without examining logs (which don't exist).

### Redesigned pseudocode

**Key principles:**
- Save to DB first — always have a record before attempting delivery.
- Enqueue email and in-app tasks separately — decouple delivery from the record of intent.
- Use a job queue with retries and failure callbacks.
- Process students in batches to avoid memory pressure.
- Log every step with structured fields.

```python
function notify_all(student_ids: array, message: string):
    # Step 1: Persist all notifications to DB first (bulk insert per batch)
    for batch in chunk(student_ids, size=1000):
        for student_id in batch:
            logger.info("Saving notification", student_id=student_id)
            save_to_db(
                student_id=student_id,
                message=message,
                notification_type="PLACEMENT",
                status="UNREAD"
            )
            # Enqueue delivery tasks (non-blocking)
            enqueue_email_task(student_id=student_id, message=message)
            enqueue_inapp_task(student_id=student_id, message=message)

function enqueue_email_task(student_id: string, message: string):
    logger.info("Enqueueing email task", student_id=student_id)
    job_queue.enqueue(
        job="send_email",
        args={ "student_id": student_id, "message": message },
        retry_count=3,
        on_failure=lambda: logger.error("Email send failed permanently", student_id=student_id)
    )

function enqueue_inapp_task(student_id: string, message: string):
    logger.info("Enqueueing in-app task", student_id=student_id)
    job_queue.enqueue(
        job="push_to_app",
        args={ "student_id": student_id, "message": message },
        retry_count=3,
        on_failure=lambda: logger.error("In-app push failed permanently", student_id=student_id)
    )
```

### Should DB save and email send happen in the same call?

**No.** They must be separated because:
- Email delivery is an external call that can fail for reasons outside our control.
- The DB record is the source of truth — it must be written regardless of delivery outcome.
- Separating them allows the DB to be updated atomically while email/in-app delivery retries independently via the queue.
- This pattern (transactional outbox) ensures no notification is silently lost.

---

# Stage 6

## Priority Inbox — Top N Unread Notifications

### Objective

Display the top `n` (default 10) most important unread notifications first. Priority is determined by:

- **Type weight**: `placement (3) > result (2) > event (1)`
- **Recency**: newer notifications rank higher within the same weight class

### Approach

1. Fetch all notifications from the evaluation API.
2. Filter to unread only (`isRead = false`).
3. Compute a **composite priority score** for each notification:

```
priority_score = type_weight × (1 + recency_factor)
```

Where:
- `type_weight` = 3 for Placement, 2 for Result, 1 for Event, 0 for unknown
- `recency_factor` = `notification_timestamp / current_timestamp` (always in (0, 1])

This formula ensures a Placement always outranks a Result of the same age, while a very recent Result can outrank a stale Placement via the recency boost.

4. Sort all unread notifications by score descending.
5. Return the top N.

### Maintaining top N efficiently as new notifications arrive

| Approach | How it works | Best for |
|----------|-------------|----------|
| **Recompute on request** | Fetch all, filter, score, sort, slice on every call | Low traffic, simple setup |
| **Redis cache** | Cache top-N per user, invalidate on new notification or read event | Medium-high traffic |
| **Redis Sorted Set** | Insert each notification with its score; `ZREVRANGE` returns top-N in O(log N) | High-volume, real-time feeds |

For this implementation, recompute-on-request is used. The Redis Sorted Set approach is recommended for production.

### Files

| File | Purpose |
|------|---------|
| `priority_inbox.py` | Main script — fetch, filter, score, display top N |
| `logging_utils.py` | Structured logging middleware used throughout |

### Running the script

```bash
pip install requests

# Top 10 (default)
python priority_inbox.py

# Top 15
python priority_inbox.py --top 15

# Top 20
python priority_inbox.py --top 20
```
