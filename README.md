# Helpware AI Bot Backend & Frontend Integration Design

**Client:** Helpware  
**Authors:** Alchemical AI  
**Date:** 2025‑09‑03

This revision integrates the verified Retell AI API and SDK usage, clarifies chat↔voice interactions, confirms conformance with Helpware's specifications, and formalizes the backend endpoints so the Helpware frontend can adopt the smallest possible change surface.

---

## 1) Scope & Goals

- Provide a **chat** experience and a **voice** (web + phone) experience powered by Retell AI.  
- Keep Helpware's existing frontend largely unchanged; expose **small, stable REST endpoints** from our backend.  
- Support **Quick Actions** ("Schedule a video meeting", "Talk to sales now", "Call me back") as first‑class flows.  
- Ensure we can **pass chat context into voice** using Retell dynamic variables.  
- Preserve a path to **warm transfer** to human agents (phone calls only).
- **Display voice conversation text back in chat** after voice sessions complete (per requirement).

---

## 2) Conformance to Helpware Design Spec

- **Floating chat button (bottom right) + CTA on scroll** — Confirmed. The helpware design doc shows a floating button in the **bottom‑right** and the CTA text extending on scroll (Page 1). We'll expose a minimal hook so the FE shows/hides the CTA label on scroll.
- **Chat overlay contents** — Logo, close, animated sphere, intro, quick actions, text input, and **Voice** button (Page 2). Spec matches and fixes quick‑action labels.
- **Quick actions** — Finalized set per the doc: **Schedule a video meeting**, **Talk to sales now**, **Call me back** (Page 2). We've removed earlier ambiguity from our internal drafts.
- **Voice mode behavior** — On clicking Voice, the overlay remains with the animated sphere; browser mic permission is required; **previous chat history must be added to voice context**; user can **Stop** the voice session; **the text of the voice conversation is displayed back in the chat** after it's completed (Page 3). All items are implemented below via Retell's Web SDK, dynamic variables, and a small transcript‑return flow.

---

## 3) Architecture Overview

**Frontend (Helpware site/webapp)**  
- Uses Retell **Web SDK** (`retell-client-js-sdk`) for web calls.  
- Calls our backend REST endpoints for: chat lifecycle, web-call access tokens, phone calls, and quick actions.

**Backend (Alchemical AI)**  
- Uses Retell **Server SDK** (`retell-sdk`) for all Retell REST calls.  
- Handles chat creation and completions, web-call token creation, phone-call creation, webhook ingestion, and integrations (HubSpot, Cal.com).  
- Summarizes chat context and injects via `retell_llm_dynamic_variables` when starting a call.

**Retell Platform**  
- Chat Agents and Voice Agents (single/multi‑prompt or conversation‑flow).  
- Transfers only in **phone** calls (not web calls).  
- Post‑call analysis & transcripts available via API/webhooks.

---

## 4) Frontend UX (Final)

1) **Floating button** (bottom‑right). FE extends CTA text on scroll.
2) **Chat overlay** includes logo, close, animated sphere, intro, quick actions, input, **Voice** button. 
3) **Typing** shows chat thread; agent replies stream in.  
4) **Voice** replaces the panel with the animated sphere; on Stop, we return to chat and show the transcript.

> **Key UX Flow**: After the voice session ends, we display the **transcript** in the chat pane (best‑effort reconstruction from events + post‑call fetch).

---

## 5) Backend REST Endpoints

> **Why one change here?** To meet the requirement "show the voice conversation text in chat afterward," the **web‑token** endpoint now returns **both** `access_token` **and** `call_id`; and we add a small **GET** to retrieve final details (transcript/analysis) after call end.

### 5.1 Chat

**Create chat**  
`POST /api/chat`  
Body:
```json
{ "agent_id": "AGENT_ID", "retell_llm_dynamic_variables": { "customer_name": "John Doe" }, "metadata": { "source": "web" } }
```
Returns:
```json
{ "chat_id": "retell_chat_id", "status": "ongoing" }
```

**Send message (create completion)**  
`POST /api/chat/{chat_id}/messages`  
Body:
```json
{ "content": "User text message" }
```
Returns (Retell echo of new messages from the agent):
```json
{ "messages": [ { "message_id": "…", "role": "agent", "content": "…" } ] }
```

**Get chat (for transcript/status)**  
`GET /api/chat/{chat_id}`  
Returns the Retell chat object (status, transcript, message history excerpt, analysis if ended).

**End chat**  
`PATCH /api/chat/{chat_id}/end` → Ends the Retell chat session.

> **Server implementation (Retell SDK):**
- `client.chat.create({ agent_id, retell_llm_dynamic_variables?, metadata? })`
- `client.chat.createChatCompletion({ chat_id, content })`
- `client.chat.retrieve(chat_id)`
- `client.chat.end(chat_id)`

### 5.2 Voice (Web Call)

**Get web‑call access token** (short‑lived; must start within ~30s)  
`POST /api/calls/web-token`  
Body (optional fields allow context handoff):
```json
{
  "agent_id": "AGENT_ID",
  "chat_id": "retell_chat_id",
  "chat_summary": "…", 
  "dynamic": { "lead_email": "…", "lead_phone": "…" }
}
```
Server behavior:
- Build `retell_llm_dynamic_variables` including `chat_summary` (computed server‑side from stored chat messages or `/api/chat/{chat_id}`) and any lead/contact state.
- Call `client.call.createWebCall({ agent_id, retell_llm_dynamic_variables })` and return both `access_token` and `call_id`.

Response (updated):
```json
{ "access_token": "JWT", "call_id": "retell_call_id", "expires_in_seconds": 30 }
```

**Get call (details/transcript)**  
`GET /api/calls/{call_id}`  
Returns final call info (transcript, analysis) once available, allowing the FE to inject the **voice conversation text back into the chat thread** exactly as helpware specifies.

### 5.3 Voice (Phone Call)

**Start outbound phone call (AI first)**  
`POST /api/calls/phone`  
Body:
```json
{
  "from_number": "+1XXXXXXXXXX",
  "to_number": "+1YYYYYYYYYY",
  "agent_id": "AGENT_ID",
  "chat_id": "retell_chat_id",
  "chat_summary": "…",
  "dynamic": { "lead_email": "…", "lead_phone": "…", "campaign": "…"} 
}
```
Server behavior:
- Call `client.call.createPhoneCall({ from_number, to_number, override_agent_id: agent_id?, retell_llm_dynamic_variables })`.  
- For **warm transfer to human**, configure the **transfer node/tool** in the agent (conversation flow); not via this endpoint.

Returns:
```json
{ "call_id": "retell_call_id", "status": "registered" }
```

> **Notes**
- `from_number` must be a Retell‑purchased/imported number.
- Warm/cold transfer is only supported in **phone** calls.
- Only **phone** calls can warm/cold transfer; this powers **Talk to sales now** when we want a human handoff.

### 5.4 Quick Actions

We'll keep **separate endpoints** for the three Quick Actions (lowest frontend change and clearer auth/policy), implemented internally by one controller if desired.

**Schedule a video meeting**  
`POST /api/actions/schedule-meeting` — "Schedule a video meeting"  
Body:
```json
{
  "contact": { "name": "…", "email": "…", "phone": "…" },
  "preferences": { "duration": 30, "time_window": "…" },
  "chat_id": "retell_chat_id"
}
```
Behavior: **May leverage Retell's native Cal.com integration** to let the AI agent directly handle scheduling within the conversation flow, or fallback to our Cal.com API integration (or pass to a Sales Queue) and return booking link/confirmation.

**Talk to sales now** (initiate outbound phone call, then agent can warm‑transfer)  
`POST /api/actions/talk-to-sales` — "Talk to sales now"  
Body:
```json
{
  "phone": "+1YYYYYYYYYY",
  "contact": { "name": "…", "email": "…" },
  "chat_id": "retell_chat_id"
}
```
Behavior: call `/api/calls/phone` with dynamic vars enriched from chat, CRM, and form fields. The voice agent will attempt warm transfer using its configured transfer node/tool.

**Call me back** (queue for AI or human callbacks)  
`POST /api/actions/callback-request` — "Call me back"  
Body:
```json
{
  "phone": "+1YYYYYYYYYY",
  "preferred_time": "2025-09-05T14:00:00-04:00",
  "contact": { "name": "…", "email": "…" },
  "chat_id": "retell_chat_id"
}
```
Behavior: enqueue in CRM with SLA; optionally auto‑dial via `/api/calls/phone` at the requested time.

Each accepts `contact` details and optional `chat_id` for context, then uses HubSpot/Cal.com as needed. **Note:** The scheduling action may utilize Retell's built-in Cal.com integration for seamless AI-driven appointment booking.

---

## 6) Frontend Integration

### 6.1 Chat (text)

Minimal changes: the FE does **not** speak directly to Retell; it calls our backend.

```ts
// Create chat
const { chat_id } = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent_id: RETELL_CHAT_AGENT_ID })
}).then(r => r.json());

// Send a user message (get agent completion back)
const { messages } = await fetch(`/api/chat/${chat_id}/messages`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: userInput })
}).then(r => r.json());
```

### 6.2 Voice (Web SDK - Enhanced with Transcript Retrieval)

Use the **Web SDK** in the browser.

```ts
import { RetellWebClient } from 'retell-client-js-sdk';

const retellWebClient = new RetellWebClient();

// When user hits the Voice button (and after mic permission):
const { access_token, call_id } = await fetch('/api/calls/web-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent_id: RETELL_VOICE_AGENT_ID, chat_id })
}).then(r => r.json());

await retellWebClient.startCall({ accessToken: access_token });

// Stop control (requires a Stop button)
function stopVoice() { retellWebClient.stopCall(); }

// Useful events for UI
retellWebClient.on('call_started', () => { /* show connected state */ });
retellWebClient.on('agent_start_talking', () => { /* animate */ });
retellWebClient.on('agent_stop_talking', () => { /* animate */ });
retellWebClient.on('update', (u) => { /* rolling transcript (last ~5 sentences) */ });
retellWebClient.on('call_ended', async () => {
  // Fetch final transcript and display in chat (requirement)
  const call = await fetch(`/api/calls/${call_id}`).then(r => r.json());
  if (call?.transcript) {
    appendSystemMessageToChat(call.transcript);
  }
});
retellWebClient.on('error', (e) => { console.error(e); retellWebClient.stopCall(); });
```

> **Token lifetime:** access token expires quickly (~30s). Only request it **right before** `startCall`.

### 6.3 Voice (phone call)

The FE calls our backend; no browser SDK involved:
```ts
await fetch('/api/calls/phone', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    from_number: RETELL_OWNED_NUMBER,
    to_number: userPhone,
    agent_id: RETELL_VOICE_AGENT_ID,
    chat_id
  })
});
```

---

## 7) Chat → Voice Context Handoff

1) **Summarize** the active chat (server‑side) and gather any structured fields (contact, interest, last QA).  
2) Include this as `retell_llm_dynamic_variables` when creating the web/phone call:  
   ```json
   {
     "retell_llm_dynamic_variables": {
       "chat_summary": "…",
       "lead_email": "…",
       "lead_phone": "…",
       "utm_campaign": "…"
     }
   }
   ```
3) The voice agent's prompt/tools must be written to **consume these variables** (e.g., greet by name, skip questions already answered, attempt transfer).

Behavior: We summarize chat server‑side and pass it via `retell_llm_dynamic_variables` so the voice agent has full context (per helpware requirement).

---

## 8) Transfers (Human Handoff)

- **Supported only in phone calls.** Configure a **Transfer Call** tool/node inside the agent with the destination(s) and handoff prompt/whisper.  
- For "Talk to sales now", we place the outbound call to the user first, then the agent warm‑transfers to the live queue when appropriate.

---

## 9) Webhooks & Analytics (Server)

### 9.1 Unified Webhook Endpoint

**Important:** Each Retell agent can only have **one webhook URL** configured. Therefore, our server must implement a **single endpoint** that handles **multiple event types**.

**Endpoint:** `POST /api/webhooks/retell`

**Event Types to Handle:**
- `call_started` - Call initiation
- `call_ended` - Call completion  
- `call_analyzed` - Post-call analysis available
- `chat_started` - Chat session initiation
- `chat_ended` - Chat session completion
- `chat_analyzed` - Post-chat analysis available

### 9.2 Implementation Pattern

```ts
// Unified webhook handler
app.post('/api/webhooks/retell', async (req, res) => {
  const { event_type, data } = req.body;
  
  try {
    switch (event_type) {
      case 'call_started':
        await handleCallStarted(data);
        break;
        
      case 'call_ended':
        await handleCallEnded(data);
        break;
        
      case 'call_analyzed':
        await handleCallAnalyzed(data);
        break;
        
      case 'chat_started':
        await handleChatStarted(data);
        break;
        
      case 'chat_ended':
        await handleChatEnded(data);
        break;
        
      case 'chat_analyzed':
        await handleChatAnalyzed(data);
        break;
        
      default:
        console.log('Unknown event type:', event_type);
    }
    
    res.status(200).json({ received: true });
  } catch (error) {
    console.error('Webhook processing error:', error);
    res.status(500).json({ error: 'Processing failed' });
  }
});
```

### 9.3 Event Processing Logic

**On `call_analyzed` or `chat_analyzed`:**
- Upsert transcript & analysis to storage
- Extract key fields (contact info, sentiment, intent, outcomes)
- Push relevant data to HubSpot (contact creation/update, deal progression)
- Trigger any scheduled follow-up actions (callback requests, meeting scheduling)
- Emit real-time notifications to frontend if session is still active

**On `call_ended` or `chat_ended`:**
- Update session status in database
- Trigger any immediate post-session workflows
- Prepare data for analysis (when `_analyzed` event arrives)

**Security Considerations:**
- Verify webhook authenticity using Retell's signature verification
- Implement rate limiting and request validation
- Ensure HTTPS-only communication
- Log all webhook events for debugging and audit trails

---

## 10) Security & Reliability

- All backend calls to Retell use the **server SDK** and API key in secure env.  
- Enforce **rate limiting**, **input validation**, **CORS** for Helpware origin(s), **HTTPS** only.  
- Handle token expiry and errors surfaced via Web SDK events.  
- Log Retell response IDs (`chat_id`, `call_id`) for observability.
- Access tokens are short‑lived; request only immediately before `startCall`.
- Store `chat_id`/`call_id` for observability; consume Retell webhooks to persist final transcripts/analysis.

---

## 11) Open Items (Helpware Confirmation)

- Confirm final **Quick Action** button labels and which flows to enable at launch.  
- **Confirm Cal.com integration approach**: Use Retell's native Cal.com integration for AI-driven scheduling, or implement separate Cal.com API integration via our backend endpoints.

---


## 12) Appendix — **Reference Snippets** (TypeScript/Express + Browser)

> These snippets are **notional** and compile in a typical Node/Express + TS setup. They demonstrate route shapes, request validation, Retell SDK calls, chat→voice handoff, and FE integration. Replace stubs with real implementations for HubSpot/Cal.com, persistence, auth, and webhook signature checks.

### 12.1 Server Setup (Express, CORS, Rate Limit, Types)

```ts
// src/server.ts
import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import Retell from 'retell-sdk';
import { z } from 'zod';

// ---- Env ----
const {
  RETELL_API_KEY,
  RETELL_CHAT_AGENT_ID,
  RETELL_VOICE_AGENT_ID,
  RETELL_OUTBOUND_FROM_NUMBER,
  FRONTEND_ORIGIN,
  PORT = '8080'
} = process.env;

if (!RETELL_API_KEY) throw new Error('RETELL_API_KEY required');

// ---- SDK ----
const retell = new Retell({ apiKey: RETELL_API_KEY });

// ---- App ----
const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(cors({ origin: FRONTEND_ORIGIN, credentials: true }));
app.use(rateLimit({ windowMs: 60_000, max: 120 }));

// ---- Types ----
type Dynamic = Record<string, unknown>;
interface Contact { name?: string; email?: string; phone?: string; }
interface SchedulePrefs { duration?: number; time_window?: string; }

// ---- Helpers ----
const asyncH =
  <T extends express.RequestHandler>(fn: T): express.RequestHandler =>
  (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function naiveSummarize(text?: string | null, max = 600): string | undefined {
  if (!text) return undefined;
  const t = text.trim().replace(/\s+/g, ' ');
  return t.length <= max ? t : t.slice(0, max) + '…';
}

async function buildDynamicVars(input: {
  chat_id?: string;
  chat_summary?: string;
  dynamic?: Dynamic;
}): Promise<Dynamic> {
  let { chat_summary } = input;
  if (!chat_summary && input.chat_id) {
    const chat = await retell.chat.retrieve(input.chat_id);
    chat_summary = naiveSummarize(chat.transcript);
  }
  return {
    ...input.dynamic,
    chat_id: input.chat_id,
    chat_summary
  };
}
```

### 12.2 Chat Routes

```ts
// src/routes/chat.ts
import { Router } from 'express';
import Retell from 'retell-sdk';
import { z } from 'zod';

export function chatRouter(retell: Retell) {
  const r = Router();

  const CreateChatSchema = z.object({
    agent_id: z.string().default(process.env.RETELL_CHAT_AGENT_ID!),
    retell_llm_dynamic_variables: z.record(z.any()).optional(),
    metadata: z.record(z.any()).optional()
  });

  r.post(
    '/',
    asyncH(async (req, res) => {
      const body = CreateChatSchema.parse(req.body);
      const chat = await retell.chat.create(body);
      res.status(201).json({ chat_id: chat.chat_id, status: chat.chat_status });
    })
  );

  const MessageSchema = z.object({
    content: z.string().min(1)
  });

  r.post(
    '/:chat_id/messages',
    asyncH(async (req, res) => {
      const { chat_id } = req.params;
      const { content } = MessageSchema.parse(req.body);
      const resp = await retell.chat.createChatCompletion({ chat_id, content });
      res.status(201).json(resp);
    })
  );

  r.get(
    '/:chat_id',
    asyncH(async (req, res) => {
      const chat = await retell.chat.retrieve(req.params.chat_id);
      res.json(chat);
    })
  );

  r.patch(
    '/:chat_id/end',
    asyncH(async (req, res) => {
      await retell.chat.end(req.params.chat_id);
      res.status(204).send();
    })
  );

  return r;
}
```

### 12.3 Calls: Web Token, Retrieve Call, Phone Dial

```ts
// src/routes/calls.ts
import { Router } from 'express';
import Retell from 'retell-sdk';
import { z } from 'zod';
import { buildDynamicVars } from '../server'; // adjust import

export function callsRouter(retell: Retell) {
  const r = Router();

  const WebTokenSchema = z.object({
    agent_id: z.string().default(process.env.RETELL_VOICE_AGENT_ID!),
    chat_id: z.string().optional(),
    chat_summary: z.string().optional(),
    dynamic: z.record(z.any()).optional()
  });

  // POST /api/calls/web-token  -> returns access_token + call_id
  r.post(
    '/web-token',
    asyncH(async (req, res) => {
      const body = WebTokenSchema.parse(req.body);
      const retell_llm_dynamic_variables = await buildDynamicVars(body);
      const webCall = await retell.call.createWebCall({
        agent_id: body.agent_id,
        retell_llm_dynamic_variables
      });
      res.status(201).json({
        access_token: (webCall as any).access_token,
        call_id: (webCall as any).call_id,
        expires_in_seconds: 30
      });
    })
  );

  // GET /api/calls/:call_id  -> retrieve call (transcript/analysis after end)
  r.get(
    '/:call_id',
    asyncH(async (req, res) => {
      const call = await retell.call.retrieve(req.params.call_id);
      res.json(call);
    })
  );

  const PhoneSchema = z.object({
    from_number: z.string().default(process.env.RETELL_OUTBOUND_FROM_NUMBER!),
    to_number: z.string(),
    agent_id: z.string().optional(),
    chat_id: z.string().optional(),
    chat_summary: z.string().optional(),
    dynamic: z.record(z.any()).optional()
  });

  // POST /api/calls/phone  -> AI dials user; agent may warm-transfer (phone only)
  r.post(
    '/phone',
    asyncH(async (req, res) => {
      const body = PhoneSchema.parse(req.body);
      const retell_llm_dynamic_variables = await buildDynamicVars(body);
      const call = await retell.call.createPhoneCall({
        from_number: body.from_number,
        to_number: body.to_number,
        override_agent_id: body.agent_id,
        retell_llm_dynamic_variables
      });
      res.status(201).json({ call_id: call.call_id, status: call.call_status });
    })
  );

  return r;
}
```

### 12.4 Quick Actions

```ts
// src/routes/actions.ts
import { Router } from 'express';
import { z } from 'zod';
import Retell from 'retell-sdk';

export function actionsRouter(retell: Retell) {
  const r = Router();

  // Schedule a video meeting
  const ScheduleSchema = z.object({
    contact: z.object({
      name: z.string().optional(),
      email: z.string().email().optional(),
      phone: z.string().optional()
    }),
    preferences: z.object({
      duration: z.number().int().positive().optional(),
      time_window: z.string().optional()
    }).optional(),
    chat_id: z.string().optional()
  });

  r.post(
    '/schedule-meeting',
    asyncH(async (req, res) => {
      const { contact, preferences, chat_id } = ScheduleSchema.parse(req.body);

      // Option 1: Use Retell's native Cal.com integration (AI handles scheduling in conversation)
      // The AI agent can directly book appointments using configured Cal.com integration
      // This may not require a separate endpoint if handled entirely within the agent flow
      
      // Option 2: Fallback to direct Cal.com API integration or Sales Queue intake
      const meetingId = 'meet_' + Math.random().toString(36).slice(2);
      const calendarLink = `https://cal.com/helpware/${meetingId}`;

      // Optionally persist the intent + meeting to CRM
      // await hubspot.createOrUpdateContact(contact);
      // await hubspot.attachEngagement(...);

      res.status(201).json({ meetingId, calendarLink, chat_id, contact, preferences });
    })
  );

  // Talk to sales now -> Outbound phone call; agent warm-transfers later (phone only)
  const TalkSchema = z.object({
    phone: z.string(),
    contact: z.object({
      name: z.string().optional(),
      email: z.string().email().optional()
    }).optional(),
    chat_id: z.string().optional()
  });

  r.post(
    '/talk-to-sales',
    asyncH(async (req, res) => {
      const { phone, contact, chat_id } = TalkSchema.parse(req.body);
      const callResp = await fetch('http://localhost:8080/api/calls/phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_number: phone,
          chat_id,
          dynamic: { lead_name: contact?.name, lead_email: contact?.email }
        })
      }).then(r => r.json());

      res.status(201).json({ ...callResp, queued_contact: contact });
    })
  );

  // Call me back -> enqueue; optionally auto-dial at preferred time
  const CallbackSchema = z.object({
    phone: z.string(),
    preferred_time: z.string().optional(), // ISO string
    contact: z.object({
      name: z.string().optional(),
      email: z.string().email().optional()
    }).optional(),
    chat_id: z.string().optional()
  });

  r.post(
    '/callback-request',
    asyncH(async (req, res) => {
      const payload = CallbackSchema.parse(req.body);
      // TODO: Persist in CRM/DB; schedule job to call at preferred_time
      const requestId = 'cb_' + Math.random().toString(36).slice(2);
      res.status(201).json({ requestId, status: 'queued', ...payload });
    })
  );

  return r;
}
```

### 12.5 Webhooks (Retell → Backend)

```ts
// src/routes/webhooks.ts
import { Router } from 'express';
// NOTE: Implement signature verification if Retell provides it.
export function webhooksRouter() {
  const r = Router();

  r.post('/retell', asyncH(async (req, res) => {
    const event = req.body; // { type: 'call_analyzed' | 'chat_analyzed' | ... }
    // TODO: persist transcript/analysis, update CRM, emit FE notifications
    // if (event.type === 'call_analyzed') { ... }
    // if (event.type === 'chat_analyzed') { ... }
    res.status(204).send();
  }));

  return r;
}
```

### 12.6 Compose the App

```ts
// src/index.ts
import { chatRouter } from './routes/chat';
import { callsRouter } from './routes/calls';
import { actionsRouter } from './routes/actions';
import { webhooksRouter } from './routes/webhooks';
import Retell from 'retell-sdk';
import app from './server-boot'; // or inline from server.ts

const retell = new Retell({ apiKey: process.env.RETELL_API_KEY! });

app.use('/api/chat', chatRouter(retell));
app.use('/api/calls', callsRouter(retell));
app.use('/api/actions', actionsRouter(retell));
app.use('/api/webhooks', webhooksRouter());

// Error handler
app.use((err, _req, res, _next) => {
  console.error(err);
  res.status( err.status || 500 ).json({ error: err.message || 'Internal Server Error' });
});

app.listen(Number(process.env.PORT || 8080), () => {
  console.log(`API listening on :${process.env.PORT || 8080}`);
});
```

### 12.7 Frontend (Browser) — Chat + Voice + Quick Actions + CTA on Scroll

```ts
// chat-ui.ts (pseudo-implementation)
import { RetellWebClient } from 'retell-client-js-sdk';

type Message = { role: 'user' | 'agent' | 'system'; content: string };
let chat_id: string | undefined;
let voiceCallId: string | undefined;
const retellWebClient = new RetellWebClient();

export async function initChat() {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: window.RETELL_CHAT_AGENT_ID })
  }).then(r => r.json());
  chat_id = resp.chat_id;
}

export async function sendUserMessage(text: string) {
  if (!chat_id) await initChat();
  const { messages } = await fetch(`/api/chat/${chat_id}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: text })
  }).then(r => r.json());
  renderAgentMessages(messages);
}

// Voice start (with mic permission)
export async function startVoice() {
  await navigator.mediaDevices.getUserMedia({ audio: true }); // triggers browser permission
  const { access_token, call_id } = await fetch('/api/calls/web-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: window.RETELL_VOICE_AGENT_ID, chat_id })
  }).then(r => r.json());

  voiceCallId = call_id;
  await retellWebClient.startCall({ accessToken: access_token });

  retellWebClient.on('update', (u: any) => {
    // u.transcript contains rolling last ~5 lines
    if (u?.transcript) renderRollingTranscript(u.transcript);
  });

  retellWebClient.on('call_ended', async () => {
    if (voiceCallId) {
      const call = await fetch(`/api/calls/${voiceCallId}`).then(r => r.json());
      if (call?.transcript) appendSystemMessage(call.transcript);
      voiceCallId = undefined;
    }
  });

  retellWebClient.on('error', (e: any) => {
    console.error(e);
    retellWebClient.stopCall();
  });
}

export function stopVoice() {
  retellWebClient.stopCall();
}

// Quick actions
export async function scheduleMeeting(contact: any, preferences?: any) {
  return fetch('/api/actions/schedule-meeting', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contact, preferences, chat_id })
  }).then(r => r.json());
}

export async function talkToSales(phone: string, contact?: any) {
  return fetch('/api/actions/talk-to-sales', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, contact, chat_id })
  }).then(r => r.json());
}

export async function requestCallback(phone: string, preferred_time?: string, contact?: any) {
  return fetch('/api/actions/callback-request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, preferred_time, contact, chat_id })
  }).then(r => r.json());
}

// Floating button CTA on scroll (PDF requirement)
const CTA_THRESHOLD = 120;
window.addEventListener('scroll', () => {
  const btn = document.querySelector('#helpware-fab')!;
  const extended = window.scrollY > CTA_THRESHOLD;
  btn.setAttribute('data-extended', String(extended)); // CSS can show/hide CTA label
});

// Simple DOM glue (pseudo)
function renderAgentMessages(msgs: Message[]) { /* … */ }
function renderRollingTranscript(t: string) { /* … */ }
function appendSystemMessage(t: string) { /* … */ }
```

### 12.8 `.env.example`

```bash
RETELL_API_KEY=sk_live_xxx
RETELL_CHAT_AGENT_ID=agent_chat_xxx
RETELL_VOICE_AGENT_ID=agent_voice_xxx
RETELL_OUTBOUND_FROM_NUMBER=+1XXXXXXXXXX
FRONTEND_ORIGIN=https://www.helpware.com
PORT=8080
```

---

**Mapping back to the PDF & Drafts**  
- Floating button with CTA on scroll (page 1) → `scroll` listener + CSS attribute.  
- Chat overlay + quick actions + Voice button (page 2) → FE functions & endpoints (Sections 12.7, 12.2–12.4).
- Voice overlay, Stop, and **transcript displayed back in chat** after completion (page 3) → `web-token` returns `call_id`, FE fetches `/api/calls/{call_id}` on `call_ended`.
- Reconciles assumptions from Markdown drafts into this final spec.
