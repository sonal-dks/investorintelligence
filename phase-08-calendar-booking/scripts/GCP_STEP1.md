# Step 1 — Google Cloud (project: `radiant-tide-495605-d1`)

## Already done from this machine

- **Gmail API** is **ENABLED** on the project (verified via Service Usage API with your service account).
- **Calendar API** could not be toggled by automation (403 — need your user in Console). Your browser should have opened the enable page.

## What you do in the browser (≈1 minute)

### A) Enable Calendar API

If a tab opened: click **Enable** for Google Calendar API.

Or open:  
https://console.cloud.google.com/apis/library/calendar.googleapis.com?project=radiant-tide-495605-d1

### B) OAuth Web client — add redirect URI

1. Open:  
   https://console.cloud.google.com/apis/credentials?project=radiant-tide-495605-d1  

2. Under **OAuth 2.0 Client IDs**, open the Web client  
   `641330500970-nb8k5i1jctpaotl66o54ea4slmchg56o.apps.googleusercontent.com`.

3. **Authorized redirect URIs** → **Add URI** → exactly:

   `http://localhost:8765/`

4. Save.

### C) Calendar sharing (still required for bookings)

Share your calendar with:

`ai-capstone-project@radiant-tide-495605-d1.iam.gserviceaccount.com`  
→ permission **Make changes to events**.

---

Re-open these URLs anytime:

```bash
open "https://console.cloud.google.com/apis/library/calendar.googleapis.com?project=radiant-tide-495605-d1"
open "https://console.cloud.google.com/apis/credentials?project=radiant-tide-495605-d1"
```
