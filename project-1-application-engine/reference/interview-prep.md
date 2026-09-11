# Interview Preparation — .NET / Azure Developer
Last updated: May 1, 2026

Load this file when preparing for a specific interview stage. Tailor to the role.

---

## Phone Screen / HR

| Question | Talking point |
|---|---|
| "Tell me about your .NET experience." | ASP.NET Core path (Big Picture → Fundamentals → MVC → EF Core → Debugging), anchor with labs. |
| "What Azure services have you worked with?" | AZ-900→AI-200 progression; call out hands-on labs specifically. |
| "Pursuing certifications?" | AZ-900 complete, AI-200 in progress (AI integration and prompt engineering focus). |
| "Why this company/role?" | 2 specific reasons — prep per company, don't generalize. |

---

## Technical Round — .NET Topics

- ASP.NET Core middleware pipeline
- Dependency injection patterns
- EF Core: migrations, relationships, performance (N+1, AsNoTracking)
- REST API design principles and versioning
- API security: JWT, OAuth2, Azure AD integration
- Debugging: structured logging, exception middleware

---

## Technical Round — Azure Topics

- Azure Functions: triggers, bindings, Durable Functions basics
- App Service vs Functions vs Container Apps — when to use each
- Azure Storage: Blob, Queue, Table — use cases
- Azure AD / Entra ID: app registrations, managed identities, RBAC
- Azure Monitor: Log Analytics, Application Insights, alerts
- Resilient architecture: retry policies, circuit breakers, health checks

---

## System Design Approach

1. Clarify requirements (functional + non-functional)
2. Sketch high-level (clients → API → services → data)
3. Map to Azure services explicitly
4. Address: scalability · security · cost optimization · monitoring
5. Call out trade-offs

**Common prompts:**
- "Design a file processing pipeline on Azure."
- "Architect a multi-tenant SaaS API on Azure."
- "Design a notification system using Azure Functions and queues."

---

## Behavioural Round (STAR format)

Pre-build answers for:
- Debugging a complex production issue
- Learning a new technology quickly
- Improving the team's development process
- Disagreeing with a technical decision — and what happened
- Mentoring or helping a colleague

> Leverage the 18 leadership/communication Pluralsight courses as evidence of intentional professional development — not just technical skills.
