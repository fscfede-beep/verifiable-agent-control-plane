# Partner ID Capture Kit — executable by human (2026-10-09)

**Status:** Partner ID UUID = STILL_NOT_RECOVERED  
**Portal:** https://partners.openai.com/  
**Role observed:** Partner Admin (case 15824755)  
**Account policy:** keep `fscfede@gmail.com` separate (Option 2)

## Why this matters

Without Partner ID, Partner Network completion and several continuity claims stay OPEN.  
This kit is the minimal human action that unblocks the gate. Grok cannot extract UI fields without your browser session.

## Capture procedure (10 minutes)

1. Open Brave Profile 3 (“Rumbo”) or the session that already has Partner Admin.
2. Go to https://partners.openai.com/
3. Navigate: **Admin / Settings / Profile** (and any Organization / Company details panels).
4. Screenshot full page (include URL bar).
5. Copy any visible:
   - Partner ID
   - Organization UUID
   - Company ID
   - Technical Assessment URL from address bar if present
6. Store screenshots offline; do **not** paste secrets into public git.
7. Reply in this chat with **only** the Partner ID / UUID values (not passwords).

## If Partner ID is not visible

Send to **partnersupport@openai.com** (and CC support if needed) using this draft:

---

Subject: RUMBO IA — Partner ID / UUID location request (correlate 15824755 / 16252998)

Hello Partner Support,

I am Sebastián, founder of RUMBO IA. Partner Admin access for RUMBO IA was confirmed (case 15824755). We still cannot locate the Partner ID / UUID in the Partner Portal UI.

- Portal: https://partners.openai.com/
- Organization/record: RUMBO IA
- Role observed: Partner Admin
- Related cases: 15824755, 16071090, 16250207, 16252998, 16553984
- Request: please point to the exact Admin/Settings/Profile (or equivalent) field that shows Partner ID/UUID, or provide the ID if available on your side.
- Account policy: keep sign-in `fscfede@gmail.com` separate/unchanged; corporate business contact path `sebastian@rumbo.verso.fans` when applicable.

Thank you.

---

## What this does NOT authorize

- Payments
- Merging ChatGPT accounts
- Product production GO
- DNS/AppDeploy changes without separate revalidation

## After capture

Return the ID here. Grok will bind it into the federation evidence plane on `federation/grok-build-primary` (hash-bound, fail-closed).
