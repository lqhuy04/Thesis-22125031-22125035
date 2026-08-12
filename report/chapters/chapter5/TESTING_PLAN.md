# Stockrium System Testing Plan

## 1. Purpose

Chapter 5 should answer whether the implemented Stockrium software behaves correctly, securely, and reliably. It should not repeat Chapter 6, which asks whether the analytical strategy performs well on historical market data.

The distinction is:

- **Chapter 5 — System Testing:** Does the software implement its requirements correctly?
- **Chapter 6 — Experiments and Evaluation:** Does the analytical pipeline exhibit useful historical behavior?

The repository now contains 71 Python `unittest` tests under `backend/tests`, covering selected multi-agent, technical, security, authentication, and backtesting behavior. Chapter 5 reports that reproducible suite. The remaining validation plan is a risk-based combination of:

1. automated backend unit and API integration tests;
2. automated mobile component and routing tests;
3. a small set of mobile end-to-end tests;
4. documented manual compatibility and usability tests;
5. focused security, reliability, and performance checks.

The final chapter must report actual results. Planned tests, unexecuted cases, and target thresholds must not be presented as passed tests.

## 2. Testing Questions

- **TQ1 — Functional correctness:** Do the mobile and backend functions produce the expected results for valid, invalid, and boundary inputs?
- **TQ2 — Integration correctness:** Do the mobile client, FastAPI services, Supabase, Redis, external data sources, and multi-agent components interact correctly?
- **TQ3 — Security and authorization:** Are authentication, session handling, ownership checks, and administrator-only functions enforced?
- **TQ4 — Multi-agent workflow reliability:** Does the multi-agent workflow honor the requested configuration, return valid structured output, and fail safely when a specialist agent or external provider is unavailable?
- **TQ5 — Quality attributes:** Is the system sufficiently responsive, compatible, recoverable, and understandable for the evaluated prototype scope?

## 3. Scope and Priorities

### P0 — Critical

- signup, email verification, login, token refresh, logout, and password recovery;
- authorization for protected routes and administrator-only routes;
- standardized API success and error responses;
- market price retrieval and stock-detail data;
- deterministic technical indicators and reference-signal calculation, multi-candle trend context, and model-generated technical scoring with fallback;
- AI-analysis configuration, structured response, model-generated confidence validation, and deterministic decision thresholds;
- chat-session ownership and deletion;
- shared technical reference scoring, AI technical-score integration, next-open execution, exit rules, and transaction costs.

### P1 — Important

- favorites, risk appetite, and search history;
- company, fundamental, article, industry, and related-stock views;
- chart rendering and period/indicator selection;
- automatic refresh after access-token expiry;
- external-service timeout and malformed-response handling;
- mobile navigation, empty states, loading states, and error messages.

### P2 — Desirable

- broader device and screen-size compatibility;
- accessibility and localization review;
- moderate API load testing;
- extended usability testing;
- long-duration collection and background-job recovery.

## 4. Recommended Test Stack

The existing backend suite uses the standard-library `unittest` runner and `unittest.mock`. The tools below are candidates for expanding coverage; they are not evidence that those tests have already been executed.

| Layer | Recommended tools | Purpose |
|---|---|---|
| Existing backend unit/integration | unittest, unittest.mock | Run the 71 repository-verifiable tests without live external providers |
| Expanded backend API/coverage | pytest, FastAPI TestClient, pytest-mock, pytest-cov | Add route-level fixtures and measure exercised code |
| Expo unit/component | Jest with jest-expo, React Native Testing Library | Test helpers, components, input validation, and user-visible states |
| Expo Router integration | expo-router/testing-library | Test navigation and route behavior in memory |
| Mobile end to end | Maestro on an Android emulator and, when available, a physical Android device | Exercise complete user flows against a test backend |
| API performance | k6 | Measure response time, error rate, and throughput under controlled load |
| Security checklist | Relevant OWASP ASVS categories | Structure authentication, session, access-control, validation, data-protection, and API checks |

Official references:

- FastAPI testing: <https://fastapi.tiangolo.com/tutorial/testing/>
- Expo unit testing: <https://docs.expo.dev/develop/unit-testing/>
- Expo Router testing: <https://docs.expo.dev/router/reference/testing/>
- Expo end-to-end testing with Maestro: <https://docs.expo.dev/eas/workflows/examples/e2e-tests/>
- k6 API load testing: <https://grafana.com/docs/k6/latest/testing-guides/api-load-testing/>
- OWASP ASVS: <https://owasp.org/www-project-application-security-verification-standard/>

## 5. Test Environment

Record the exact environment in the final chapter:

- test date and code revision;
- Windows, Python, and Node versions;
- FastAPI, Expo, React Native, browser, emulator, and device versions;
- Android emulator/device model, API level, screen size, and network mode;
- backend base URL and whether it is local or staged;
- database and Redis test instances;
- external-service mode: mocked, sandbox, or live;
- fixed test symbols and data interval;
- model name, prompt version, temperature, and random seed where supported.

Use an isolated Supabase test project or test schema and a separate Redis database. Never run destructive test cases against production data. Create dedicated fixtures for:

- one verified ordinary user;
- one unverified user;
- one administrator;
- a second ordinary user for ownership tests;
- one expired or revoked token.

Use fixed OHLCV, company, fundamental, and article fixtures. Mock SSI, Serper, Resend, social OAuth, OpenAI, and DeepSeek for automated tests. A few separately identified live-provider smoke tests may be run, but their variable outputs should not determine whether the regression suite passes.

## 6. Test Design

Apply these techniques:

- **equivalence partitioning:** valid, invalid, missing, and unauthorized requests;
- **boundary analysis:** dates, pagination, score thresholds, weights, holding periods, OTP limits, and empty datasets;
- **state-transition testing:** signup to verification, access-token expiry to refresh, chat creation to deletion, and backtest request to stored artifact;
- **decision-table testing:** enabled agents, weights, confidence bands, roles, and ownership;
- **fault injection:** provider timeout, malformed JSON, empty database response, unavailable Redis, and partial agent failure;
- **regression testing:** rerun the critical suite after every fix.

## 7. Proposed Test Matrix

The matrix below is the minimum useful thesis scope. Detailed steps should be recorded in a spreadsheet or appendix; Chapter 5 should summarize representative cases and aggregate results.

| ID | Area | Scenario | Expected result | Priority | Method |
|---|---|---|---|---|---|
| AUTH-01 | Signup | Submit valid new account | Account created; verification process starts; standardized response returned | P0 | API integration |
| AUTH-02 | Signup | Duplicate email or invalid password/email | Correct rejection and no duplicate account | P0 | API integration |
| AUTH-03 | Verification | Correct, incorrect, expired, and reused OTP | Only the current valid OTP verifies the account | P0 | API integration |
| AUTH-04 | Login | Valid and invalid credentials; unverified account | Token pair issued only for allowed credentials and account state | P0 | API integration |
| AUTH-05 | Session | Expired access token with valid refresh token | One refresh occurs and the original request is retried successfully | P0 | API + mobile integration |
| AUTH-06 | Session | Revoked/expired refresh token and logout | Session ends, protected calls fail, and secure tokens are removed | P0 | API + mobile E2E |
| AUTH-07 | Password | Forgot-password, OTP limits, reset, and old credential attempt | Reset rules and cooldowns are enforced | P0 | API integration |
| SEC-01 | Authorization | Ordinary user calls admin analysis, universe, backtest, or listing | 401/403 response and no operation | P0 | API integration |
| SEC-02 | Ownership | User A accesses User B's chat or owned resources | Rejected with User B's data unchanged | P0 | API integration |
| SEC-03 | Input handling | Malformed symbols, UUIDs, dates, payloads, large text, and injection-like values | Safe validation with no internal-detail leak | P0 | API/security |
| API-01 | Contract | Representative success and failure from every router | Standard data, errorCode, errorDesc, requestId, and result fields | P0 | Contract tests |
| DATA-01 | Market | Valid symbol and date range | Ordered OHLCV schema without duplicates | P0 | Service/API integration |
| DATA-02 | Market | Unknown symbol, empty interval, or provider failure | Clear empty/error response; service remains available | P0 | Fault injection |
| DATA-03 | Fundamentals | Profile, leaders, statements, ratios, and summary | Records match fixed database fixtures | P1 | API integration |
| DATA-04 | Articles | Stock, category, macro, business, and highlight queries | Correct filtering, ordering, pagination, and associations | P1 | API integration |
| TECH-01 | Indicators | RSI, SMA, Bollinger Bands, MACD, and KDJ from fixed candles | Values match independently prepared expected values within tolerance | P0 | Unit test |
| TECH-02 | Indicators | Insufficient candles, missing values, constant prices, and zero volume | Defined empty/null behavior and no crash | P0 | Unit/API |
| USER-01 | Preferences | Read and update risk appetite | Value persists only for the authenticated user | P1 | API + mobile |
| USER-02 | Favorites | Add, duplicate-add, check, list, and delete | Idempotent state and correct enriched data | P1 | API + mobile |
| USER-03 | Search history | Add, deduplicate, list, cap, and clear recent searches | Correct ownership, persistence, ordering, and empty states | P1 | API + mobile |
| AGENT-01 | Orchestration | Automatic/manual modes and enabled branches | Only selected specialists run and weights normalize correctly | P0 | Integration with mocks |
| AGENT-02 | Structure | Mock specialists return valid evidence | Aggregator output satisfies the typed schema and API contract | P0 | Integration with mocks |
| AGENT-03 | Decision | Weighted total and technical score below, at, and above their acceptance thresholds | Buy/Wait control follows both deterministic boundaries; confidence does not alter it | P0 | Unit test |
| AGENT-04 | Horizon | Short-, medium-, and long-horizon profiles | Planning and holding constraints match the selected horizon | P0 | Integration with mocks |
| AGENT-05 | Failure | Specialist timeout, malformed output, or no evidence | Defined fallback or safe error; no unsupported recommendation | P0 | Fault injection |
| CHAT-01 | Conversation | Create, continue, reopen history, and delete | Ordered owner-only history and complete deletion | P1 | API + E2E |
| BACK-01 | Shared scoring | Known indicator values through the shared scorer and both adapters | Production output and backtest score columns use the shared rule results | P0 | Unit/integration |
| BACK-02 | Warm-up | Full and single-indicator runs use a later evaluation start | Pre-start history is retained, the shared 50-candle warm-up is preserved, and trimming occurs after scoring | P0 | Unit/integration |
| BACK-03 | Timing | Score meets threshold on candle t | One candidate and entry at candle t+1 open | P0 | Unit test |
| BACK-04 | Rules | Take-profit, stop-loss, score exit, max hold, final liquidation | Correct reason, date, price, cost, and return | P0 | Parameterized unit |
| BACK-05 | Edges | Same-bar TP/SL, gap, final signal, no candidates, missing benchmark | Conservative documented behavior and no invalid trade | P0 | Unit/integration |
| BACK-06 | Artifacts | Complete backtest and result listing | Decisions, trades, metrics, effective warm-up metadata, tests, plots, and stored file agree | P1 | Integration |
| MOB-01 | Authentication UI | Signup/login, verification, reset, logout | Correct validation, feedback, loading, and navigation | P0 | Component + E2E |
| MOB-02 | Market UI | Browse, search, open detail, change chart view | Correct data, navigation, and responsive interaction | P0 | Component + E2E |
| MOB-03 | AI analysis UI | Configure, submit, and view result | Correct payload and safe rendering of all structured fields | P0 | Component + E2E |
| MOB-04 | Resilience | Offline, slow, 401, 500, and empty data | Clear retry/error/empty state and no duplicate submission | P1 | Component + manual |
| MOB-05 | Presentation | Themes, Vietnamese text, long content, keyboard, small screen | Readable layout without clipping or blocked actions | P1 | Manual/device |
| PERF-01 | API load | Health, market, detail, login, and preference flows | Provisional thresholds in Section 8 are met | P2 | k6 |
| REL-01 | Recovery | Restart Redis/backend or interrupt a provider | Controlled error/recovery and no corrupted state | P1 | Fault injection |
| USE-01 | Usability | Users complete discovery, analysis, favorite, and chat tasks | Completion, errors, time, and clarity ratings recorded | P2 | Observed study |

## 8. Provisional Acceptance Criteria

These are targets, not current results:

- all P0 cases pass;
- at least 95% of executed P1 cases pass, with every failure documented;
- no unresolved critical or high-severity security or authorization defect;
- all tested protected and administrator-only routes reject invalid roles or tokens;
- target at least 80% automated statement coverage for deterministic authentication, scoring, decision, trading-plan validation, and backtesting modules; report the actual value even if lower;
- critical mobile E2E flows pass three consecutive runs without a flaky failure;
- at 20 concurrent virtual users in the stated local/staging environment, non-AI requests have under 1% unexpected errors, p95 below 500 ms for simple reads, and p95 below 1 s for ordinary writes;
- AI and backtesting latency are reported separately because provider time and experiment size dominate them;
- no data loss or cross-user exposure during recovery and ownership tests.

Performance thresholds may be revised before execution, but must be frozen before examining final measurements.

## 9. Execution Plan

### Phase 1 — Freeze and trace requirements

1. List requirements from Chapters 1 and 3.
2. Map each requirement to at least one test ID.
3. Mark P0/P1/P2 and define defect severity.
4. Freeze the tested commit and environment.

### Phase 2 — Establish infrastructure

1. Create isolated database and Redis test instances.
2. Add fixed financial-data fixtures and test users.
3. Add backend pytest configuration and shared fixtures.
4. Add Expo Jest configuration outside the app route directory.
5. Create mock adapters for external providers.

### Phase 3 — Backend tests

1. Test deterministic utilities.
2. Test authentication and authorization.
3. Test market, company, fundamental, article, and user-data routes.
4. Test the standardized response contract.
5. Test multi-agent and backtesting logic with fixed model outputs.

### Phase 4 — Mobile tests

1. Test form validation and API helpers.
2. Test loading, success, empty, and failure states.
3. Test token-refresh coordination.
4. Test core Expo Router navigation.

### Phase 5 — End-to-end smoke suite

Automate these flows first:

1. login and logout;
2. search and open stock details;
3. add and remove a favorite;
4. configure and submit AI analysis against a deterministic test backend;
5. create a chat, continue the conversation, reopen it, and delete it.

### Phase 6 — Non-functional tests

1. Run role, ownership, validation, and information-disclosure checks.
2. Run moderate API load tests in isolation.
3. Check selected Android screens and one slow-network profile.
4. Observe representative users completing core tasks.
5. Perform restart and provider-failure tests.

### Phase 7 — Correction and regression

For every defect, record severity, requirement, reproduction steps, fix revision, and retest result. Rerun all P0 tests after corrections.

### Phase 8 — Write Chapter 5 from evidence

Collect command output, coverage summaries, result tables, selected request/response samples, mobile screenshots, the k6 summary, device matrix, usability task summary, and defect/retest records.

## 10. Suggested Ten-Day Schedule

| Day | Work |
|---|---|
| 1 | Traceability, priorities, environment, and test data |
| 2–3 | Backend harness, deterministic tests, authentication, authorization |
| 4 | Data-domain and API-contract tests |
| 5 | Multi-agent and backtesting correctness/failure tests |
| 6 | Expo Jest setup, helpers, forms, routing, and UI states |
| 7 | Five Maestro end-to-end flows |
| 8 | Security, performance, recovery, and device checks |
| 9 | Fixes, regression, coverage, and evidence capture |
| 10 | Chapter 5 tables, discussion, and limitations |

If time is limited, complete P0 backend/API tests, three core mobile E2E flows, authorization checks, and one controlled performance test before expanding P1/P2.

## 11. Final Chapter 5 Structure

1. **Testing Objectives and Scope**
   - distinction from Chapter 6;
   - testing questions;
   - included and excluded areas.
2. **Test Strategy and Environment**
   - levels, techniques, tools, environment, test data, and mocking;
   - requirement-to-test traceability.
3. **Backend Functional and Integration Testing**
   - authentication and authorization;
   - financial-data APIs and response contract;
   - user-owned resources.
4. **Multi-Agent and Backtesting Correctness Testing**
   - branch selection, weights, typed output, confidence boundary;
   - shared scoring, timing, exits, costs, and failure cases.
5. **Mobile Application and End-to-End Testing**
   - component and routing results;
   - critical end-to-end flows;
   - device and presentation checks.
6. **Non-Functional Testing**
   - security, performance, recovery, compatibility, and usability.
7. **Results and Defect Analysis**
   - totals by area and priority;
   - pass/fail rates;
   - defects, corrections, and regression.
8. **Testing Limitations and Summary**
   - untested platforms or providers;
   - mock-versus-live limitations;
   - remaining risks.

## 12. Recommended Result Tables

### Overall summary

| Area | Planned | Executed | Passed | Failed | Blocked | Pass rate |
|---|---:|---:|---:|---:|---:|---:|
| Authentication and security | | | | | | |
| Market and financial data | | | | | | |
| User-owned resources | | | | | | |
| Multi-agent workflow | | | | | | |
| Backtesting correctness | | | | | | |
| Mobile application | | | | | | |
| Non-functional | | | | | | |

Calculate pass rate as Passed / Executed, not Passed / Planned. Report blocked and unexecuted cases separately.

### Representative case

| Field | Content |
|---|---|
| Test ID | |
| Requirement | |
| Preconditions | |
| Input and steps | |
| Expected result | |
| Actual result | |
| Status | Pass / Fail / Blocked |
| Evidence | Screenshot, log, response, or artifact ID |
| Defect/retest | |

### Defect summary

| Defect ID | Severity | Area | Description | Correction | Retest |
|---|---|---|---|---|---|

## 13. Reporting Rules

- Do not invent pass counts, coverage, response times, devices, or usability results.
- Keep raw evidence outside the thesis and cite artifact identifiers in the chapter.
- Show representative cases in Chapter 5 and put the complete list in an appendix or repository artifact.
- Report failed and blocked tests, not only successful cases.
- Separate Stockrium failures from unavailable external-provider failures.
- State when a dependency is mocked; do not describe a mocked test as a live-provider test.
- Do not use Chapter 5 test success as evidence that recommendations are profitable.
