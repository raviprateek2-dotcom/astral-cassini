# PRO HR API Documentation

## Authentication & Security
The backend uses Cookie-based session authentication with CSRF double-submit tokens.
* `POST /api/auth/login`: Authenticates the user and sets an `access_token` HttpOnly cookie. Requires `x-csrf-token` header for mutating state.
* Rate Limiting: Strict rate limiting (`5/minute`) is enforced on the login endpoint.

## Job Pipeline Lifecycle (`/api/jobs`)
Endpoints to trigger and manage state machine transitions:
* `POST /api/jobs/`: Creates a new job requisition and initializes the state machine (`jd_drafting`).
* `GET /api/jobs/`: Lists all active pipelines for the user.
* `GET /api/jobs/{job_id}`: Retrieves full state of a pipeline.
* `POST /api/jobs/{job_id}/approve_jd`: Approves the JD draft, transitioning the pipeline to `sourcing`.
* `POST /api/jobs/{job_id}/approve_shortlist`: Approves candidate shortlist, triggering `interviewing`.
* `POST /api/jobs/{job_id}/approve_hire`: Approves final candidates, completing the pipeline.
* `DELETE /api/jobs/{job_id}`: Deletes a pipeline permanently.

## WebSocket Real-Time Feed (`/ws/{job_id}`)
Connected clients receive real-time streams of agent reasoning and stage changes.
* **Connection**: Requires a short-lived ticket from `GET /api/auth/ws-ticket/{job_id}`.
* **Events**:
  * `connected`: Sent upon successful authentication.
  * `stream_token`: Live text chunk from JD Architect.
  * `pipeline_update`: Emitted when the state machine completes a stage transition.
  * `heartbeat`: Broadcasts pipeline summary metrics.
  * `ping` / `pong`: Used to verify connection health.
