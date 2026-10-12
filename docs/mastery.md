# Server-verified checks and transparent mastery (Phase 5)

## Owned backend contract

This implementation owns `backend/mastery.py`, `backend/routes/learning.py`,
`tests/test_learning.py` and this document. It does not change `main.py`, shared
models, progress routes, frontend files, seed scripts, migrations or `.env`.

All three learning endpoints require `get_current_user`. There is no public
endpoint accepting a client-supplied score, correctness, user ID or concept ID.

| Endpoint | Request | Response |
| --- | --- | --- |
| `GET /learning/{topic_slug}/checks` | Authenticated GET | `{topic_slug, checks: [...]}` |
| `POST /learning/{topic_slug}/check` | `{block_id, selected_index}` | `{correct, explanation, mastery}` |
| `GET /learning/{topic_slug}/mastery` | Authenticated GET | The current mastery summary |

`selected_index` must be an actual JSON integer from 0 through 19, not a boolean,
string or float, and must address an option in the selected check. IDs and slugs
are limited to 128 characters. Extra request properties are rejected. Missing
topics/checks return 404; invalid selections return 422; malformed trusted checks
or unavailable built-in curriculum return a sanitized 503. Database errors remain
driver exceptions for the application's existing sanitized database handler.

The server fetches the **trusted full topic**, locates the specified quiz across
top-level blocks and all subtopics, compares against its stored `correct_index`,
and records 100 for correct / 0 for incorrect. Only the submitted check's
explanation is returned after the evidence write succeeds. The mastery response
does not include answer indices or protected explanations.

## Shared lookup and stable IDs

Use these public Python helpers from `backend.mastery`:

- `await load_topic(topic_slug)`: query the shared MongoDB `topics` catalog first.
  Only a missing topic (`None`) falls back to the full validated, version-controlled
  `backend.curriculum.load_curriculum()` result. Database errors do **not** silently
  fall back. No stripped browser JSON or interview benchmark data is used to grade.
- `serialize_checks(full_topic)`: return the safe checks list. Requires trusted full
  content; do not pass already-stripped public content into it.
- `topic_checks(full_topic)`: internal normalized checks **including protected
  grading fields**. Never return this helper's output directly to a browser.

Each safe check contains `id` (an alias of `block_id`), `block_id`, `concept_id`,
`question`, `options`, `subtopic_index` and `block_index`. It is a whitelist; neither
`correct_index`, `explanation`, nor unknown answer metadata is copied.

The identity convention is exact and zero-based:

1. Check identity: nonempty `block.block_id`, otherwise `block.id`.
2. Legacy subtopic check: `legacy:subtopic:{subtopic_index}:block:{block_index}`.
3. Legacy top-level check: `legacy:topic:block:{block_index}`.
4. Concept identity: `block.concept_id`, otherwise the containing section's
   `concept_id`, otherwise `legacy:subtopic:{subtopic_index}` / `legacy:topic`.

Block indices count **all content blocks**, not just quizzes. Top-level checks
have `subtopic_index: null`. Duplicate check IDs within a topic fail closed; the
server never picks the first of several ambiguous checks. Explicit IDs are strongly
preferred. Legacy coordinates are stable only while the lesson order remains the
same. Reordering legacy blocks or changing an answer/concept should assign new
explicit IDs to prevent reusing outdated evidence. Identical question text is not
an identity; frontend question matching should require a unique match or use the
returned coordinates.

## Heuristic and reassessment policy

Mastery is a transparent heuristic, **not** a calibrated probability, an AI grade,
or proof of durable learning. Assessments, not reading/completion toggles, determine
it. Scores are percentages from 0 to 100.

For every `(kind, source_id)` only the latest committed evidence remains. Repeating
one quiz refreshes/replaces that check; it does not add attempts, distinct quiz
coverage or extra points. A later incorrect answer replaces an earlier success.
Quiz and coding namespaces are separate, so an identical source ID across the two
kinds cannot overwrite unrelated evidence. Unknown/removed quiz IDs and concept
mismatches are ignored when computing current mastery.

Evidence is fresh for **less than 14 days** after its recorded UTC timestamp. At
exactly 14 days it expires. Scores/coverage are calculated anew on every GET, so a
previously mastered lesson can become `review` without a background job or write.
MongoDB naive datetimes are treated as UTC. A five-minute forward clock-skew
tolerance is allowed; larger future timestamps are not fresh. Stale evidence is
retained for feedback but contributes no score or coverage.

Default coding lesson requirements are all mandatory:

- At least **two distinct fresh quiz checks**, quiz mean **>= 80**.
- At least one fresh **server-verified coding** source, coding mean **>= 80**.
- Every concept represented by a current quiz must have fresh quiz evidence with
  mean >= 80. Cover at least two concepts when available; a one-concept lesson
  requires that one, but still needs two distinct checks.
- Overall score is `0.5 * quiz_mean + 0.5 * coding_mean`, treating a missing kind
  as zero, and must be >= 80. An excellent quiz cannot compensate for failed coding.
- If coding is attributed to a known concept, that concept's coding mean must
  also be >= 80. Unattributed coding satisfies only the topic-level coding gate.

An author can explicitly opt a **noncoding MongoDB lesson** into
`mastery_policy: {coding_required: false}`. It then needs **three distinct fresh
quizzes**, quiz mean >= 80 and the same concept coverage. Its overall score is the
quiz mean; optional coding does not affect its mastery or concept scores. Do not infer this policy from missing practice
problems, which might simply mean an incomplete catalog. The current strict
built-in curriculum schema does not support this additional metadata; its owner
must extend the schema before opting built-in noncoding lessons in.

Topic state is `mastered` only when every applicable gate passes. Otherwise it is
`weak` with no retained evidence or with fresh below-80 assessment evidence, and
`review` when the issue is missing coverage, stale evidence, or reading-only
activity. A concept can have a passing assessment state without the topic being
mastered; each concept includes score/kind scores and reasons. Reading is counted
as activity but **never** enters numeric mastery or assessment coverage.

The summary includes `score`, `status`, `quiz_score`, `coding_score`, policy/minimums,
`concepts`, `reasons`, fresh `evidence_counts`, `retained_evidence_count`,
`review_after`, `missed_questions` and `next_activity`. `review_after` is a conservative
earliest expiry for a currently mastered topic. A next activity prioritizes an
unseen/missed/stale quiz, then missing/weak coding, then periodic review. Insufficient
distinct content recommends more lesson checks rather than gaming repetitions.
Latest incorrect quizzes appear in `missed_questions`, including their safe
question/options/IDs, score, timestamp and reassessment flag. A correct retry removes
the missed item. Enough alternative fresh evidence can satisfy a concept even if
an additional source is stale; not every individual quiz must be perfect.

## Evidence storage and practice integration

Public async API for trusted backend callers:

```python
from backend.mastery import record_evidence

mastery = await record_evidence(
    user_id, topic_slug, kind, score, source_id, concept_id=None
)
```

Supported kinds are `quiz`, `coding`, `reading`. Scores must be finite numeric values
in [0, 100], never booleans. `user_id` must be a MongoDB ObjectId or its hexadecimal
string. Quiz sources/concepts must match the trusted current catalog. A coding
caller must already have executed and verified the work server-side; this function
does not run code or prove an arbitrary caller's grade. Use the persistent practice
problem ID as the source, **not a new submission/attempt ID**. The practice agent's
`record_evidence(current_user["id"], topic_slug, "coding", score, source_id=problem_id)`
call is supported without a concept ID. This API returns the same mastery summary.

`user_mastery` has one canonical document per user/topic, identified by
`"mastery:v1:" + sha256(str(ObjectId(user_id)) + "\0" + topic_slug)`. The existing
MongoDB unique `_id` index prevents concurrent initial upserts from creating multiple
canonical documents. Every personal read/update filter includes `_id`, `user_id`
and `topic_slug`; a duplicate-key insert race retries **once** with the same scoped
key and `upsert=False`. No unscoped fallback read or automatic index build occurs.
Shared topic catalog lookups use the slug, since catalog topics have no per-user
owner; they are reached only after route authentication.

A single `find_one_and_update(..., return_document=AFTER)` aggregation-pipeline
operation filters out the old `(kind, source_id)`, appends the new evidence, and
retains the last **64 distinct sources**. `$$NOW` supplies the server operation time;
strings are `$literal` expressions, not executable aggregation paths. There is no
read/modify/write race, unbounded attempt log or stored derived mastery cache.
Evidence rows contain only kind, source ID, concept ID, score and timestamp; no
answers, submitted code, credentials or profile data. See MongoDB's
[pipeline update documentation](https://www.mongodb.com/docs/manual/reference/method/db.collection.findandmodify/)
and [single-document atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/).

Requires MongoDB **4.2+** pipeline updates. The cap can evict older sources even
before 14 days; lessons with more than 64 required quiz sources/concepts need a
separate retention design. Existing noncanonical legacy mastery documents are not
read, deleted or migrated. A database timeout can leave write outcome uncertain;
retrying the same source replaces it rather than incrementing coverage. Mocked
tests assert pipeline shape and model atomic replacement, not real server semantics.

## Integration owned by main/frontend agents

1. Import `learning` from `backend.routes` and call
   `app.include_router(learning.router)` in `main.py`.
2. Keep public content answer redaction for **both** MongoDB and built-in fallback
   paths. Preserve question/options/explicit `id`/`block_id`/`concept_id`. Use the
   same full trusted `load_topic()` lookup for published content where practical;
   never feed stripped public responses back into the grader.
3. Authenticated `topic.js` fetches `/learning/{slug}/checks`, matches stable IDs
   (or uniquely matched legacy questions/coordinates), and POSTs only the returned
   `block_id` plus integer `selected_index`. Render the server result and mastery;
   do not compare against a browser answer key. Treat all content as text.
4. Public visitors may read questions/options but should see sign-in assessment,
   not local grading. Learning endpoints intentionally return 401 without a user.
5. Keep client progress/completion separate from mastery. The progress route owner
   must not equate reading or a status toggle with `mastered`. Wire authenticated
   mastery/review UI to this server summary, not client-supplied scores.
6. Apply any required rate limiting using the existing application policy. Distinct
   evidence prevents repetition-based score inflation, but it does not stop brute
   force, memorization after feedback or unlimited HTTP requests.

## Validation

```text
python -m unittest discover -s tests -p test_learning.py -v
```

Tests use synthetic modules instead of the real config/auth/database imports,
mocked Motor operations, and in-process ASGI requests. No secrets, `.env`, real
MongoDB, seeds, migrations, remote execution or live model calls are used. Run
outside the Windows sandbox because asyncio's internal loopback sockets can hang
there. A deployment-matched MongoDB/driver integration test remains required before
release; no live database was changed during this task.

Validation passed **36 focused mocked tests**. An additional offline check loaded
the current built-in curriculum: **15 topics / 30 checks** successfully normalized,
with no answers or explanations in the public serialization. The available local
runtime was Python 3.14, not the declared Render Python 3.11 runtime.
