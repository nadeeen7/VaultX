# VaultX production OTP delivery diagnosis

## Confirmed source findings

GitHub `main` was `d103233ea0d4a8e7e4526eb4adcf19e2b7592c0a` when inspected. Its `bank/backend/app/services/email_service.py` already includes the Resend HTTPS adapter. `send_otp_email()` resolves the transport and invokes `_send_via_api()`, which POSTs to `https://api.resend.com/emails` with a Bearer key, sender, recipient, text and HTML. The existing end-to-end mocked transport test exercises request, verification, reset and login.

`EMAIL_PROVIDER=resend` forces Resend and reads `RESEND_API_KEY`. Sender selection is `MAIL_DEFAULT_SENDER`, with `RESEND_FROM` as a legacy fallback. An explicitly selected different provider overrides the presence of a Resend key. With no explicit provider, selection tries Resend, Brevo, SendGrid, then SMTP. Unknown provider values currently also fall through to auto-selection; this diagnostic patch preserves that behavior and reports them as `invalid`.

The old startup log could wrongly describe HTTP delivery when SMTP was explicitly selected but an API key was also present. This patch logs the actual resolved provider.

On the inspected, unpatched revision, the exact generic HTTP 200 can result from an early return before email dispatch, or from acceptance by whichever provider was selected. Unknown and Google-only account paths intentionally do not send OTPs. The cooldown path used a different 200 message; transport failures returned 503. Therefore a missing key or Resend rejection on that revision is not, by itself, consistent with the exact generic 200 from an eligible send attempt.

A direct Resend email marked Delivered proves that independent send worked. It does not prove VaultX selected Resend, used the same provider account, or reached its dispatch code.

## What this patch changes

- Internal JSON diagnostics at startup and throughout the reset/email request, correlated by a random server-generated trace ID.
- Configuration logs contain allowlisted provider labels, presence flags, missing variable names, and a validated Render commit SHA if available.
- Provider results contain HTTP status or exception type only. No response bodies, exception messages, recipient addresses, OTPs, credentials, headers, or mail contents are logged.
- Cooldown and provider-failure responses now use the same generic 200 as other valid reset requests to avoid public eligibility disclosure. Validation and request-rate-limit responses are preserved. Internal logs retain delivery failures.
- OTP generation, hashing, expiry, attempts, single-use verification and password-reset logic are unchanged. Synchronous delivery timing is unchanged; this patch does not claim timing-side-channel elimination.

## Production check, without sharing secrets

In the **Bank API service** `vaultx-bank-api`, confirm the deployed revision contains the adapter and, after publication, this diagnostic patch. GitHub main alone does not identify Render's active revision. Set `EMAIL_PROVIDER` to `resend`. Configure the existing `RESEND_API_KEY` and verified `MAIL_DEFAULT_SENDER` privately in Render; never paste their values into chat or logs. Changes must apply to the backend, not the frontend or SIEM service.

After redeployment, the internal `configuration` record should show:

- `configured_provider`: `resend`
- `selected_provider`: `resend`
- `resend_key_present`: `true`
- `default_sender_present`: `true`
- `missing`: empty list

Perform one normal password-reset request for your own account. Use the internal trace to interpret the result:

| Log outcome | Meaning |
| --- | --- |
| No `reset_request` | Request did not reach this instrumented route, was rejected earlier, or the patch is not deployed. Verify the browser request's backend hostname and Render revision. |
| `reset_result=not_dispatched` | The existing eligibility/cooldown rules skipped sending. No email API call is expected. No identifier or specific eligibility reason is logged. |
| `selected_provider` differs from `resend` | Actual backend provider configuration mismatch. |
| `selected_provider=none` | Required transport configuration is missing; logs name variables only. |
| `transport_attempt` with `provider=resend` | VaultX is invoking the Resend HTTPS endpoint. |
| `transport_result=rejected` | Provider returned a non-success status. Investigate that status privately in the hosting/provider console. |
| `transport_result=exception` | Transport raised the logged exception type; the body/message is deliberately omitted. |
| `transport_result=accepted` | Resend returned a success status; this does not establish inbox delivery. Confirm the API key belongs to the same account/workspace whose Emails view you inspect. |

Do not infer account existence from a public response or publish private delivery logs. Do not bypass OTP checks to debug delivery.

## Validation and limits

64 Bank tests pass (58 existing plus 6 diagnostic/privacy checks), including the real application route through a mocked Resend HTTP call, OTP verification, reset and subsequent login. Test email data and keys are synthetic; no production OTP was sent. Database credentials and production data were not changed.

Render's active environment, deploy revision and request logs were not available to this session. A public health request timed out. Consequently the exact production cause is **not yet established**. The new diagnostic stages distinguish skipped dispatch, wrong transport, missing config, rejection and acceptance without exposing mail data. Safe configuration/stage records from the deployed patch are the remaining evidence needed; no secret values are needed.
