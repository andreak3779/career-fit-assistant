<!-- GENERATED FILE — do not hand-edit. Regenerate via profile-hub-bundle-generator skill. -->
# Presence Bundle — Sarah Ashford
bundle_version: 20
generated: 2026-09-11

---
## Copy Fragments
course_count_sentence: "225 Pluralsight courses completed and 49 more in progress, plus 30 hands-on labs (30 completed, 0 in progress) — 304 total"
cert_status_short: "AZ-900 Certified · AI-200 in progress"
azure_course_lab_sentence: "36 Pluralsight courses and 19 hands-on labs across Azure"
github_copilot_course_count: "19"
leadership_course_count: "19"

---
## Professional Headline

**Senior Full-Stack .NET Developer | Enterprise Applications | 9+ Years**

Technology professional who bridges legacy modernization and cloud-native delivery.

## Summary / About

Full-stack .NET developer with a track record of modernizing legacy enterprise systems into service-oriented, cloud-hosted applications. Comfortable owning a feature from database schema through Angular UI through CI/CD pipeline, with particular depth in insurance and manufacturing domains.

## Cert Status + Badge URLs

| Cert | Status |
|---|---|
| AZ-900 | **Certified April 18, 2026** — [Credential](https://learn.microsoft.com/api/credentials/share/en-ca/SarahAshford-1234/7A3C2E19B4F0D821?sharingId=4C91E7A2B0D3F5C6) |
| AI-200 | **Active target** — exam available July 2026; **Azure Cosmos DB Deep Dive completed 100% (May 27, 2026)** — closes the primary Domain 2 gap; **Vector Databases & Embeddings for Developers completed 100% (Jul 14, 2026)** — closes Domain 2 vector-DB/RAG coverage; **Microsoft Certified: Azure Developer Associate (AZ-204): Develop Azure Compute Solutions completed 100% (Aug 26, 2026)** — deepens Azure compute-solutions coverage; ⚠️ "10 courses actively in progress" needs reconfirmation — JSON-only Azure-keyword matching finds 6 in-progress Azure courses as of Aug 26, 2026 (highest now: Using EF Core 6 with Azure Cosmos DB, 32%; Architectural Considerations for Azure Monitoring, Automation, and Cost Management, 7%); the original 10-course figure was curated by topical relevance to AI-200 (e.g. FastAPI Foundations, MongoDB), not by title keyword, so it doesn't reduce cleanly from JSON alone. Up and Running with Kusto Query Language (KQL) plus two additional KQL courses (Filter and Search Data, Summarize and Aggregate Data) all completed — deepens Domain 4 query/monitoring coverage. Introduction to Developing AI Agents + Domain-specific LLM Agents completed Jun 2026; Claude series (Introduction to Claude, Claude Best Practices, Prompting Basics for Claude, Claude Practical Applications, Claude Advanced Features) all completed Jun 26, 2026 — deepens LLM API integration and prompt engineering domains |

## Technical Skills (flat list, ATS-formatted)

### Backend Development
C#, ASP.NET Core, .NET Framework, Entity Framework Core, LINQ, Web API, REST, dependency injection, async/await, service-oriented architecture

### Frontend & UI
Angular (v12+), TypeScript, RxJS, Angular Material, HTML, CSS/SASS, Jest

### Database & SQL
SQL Server, T-SQL, DB2, query optimization, Entity Framework migrations

### Cloud & Azure
Azure App Service, Azure DevOps Pipelines, Azure Application Insights, Azure AD

### DevOps & CI/CD
Docker, GitLab CI, Azure Pipelines, SonarQube, code review process ownership

### Testing
xUnit, Moq, Jest, integration testing, test coverage improvement initiatives

### Project Management & Agile
Scrum, sprint planning, story pointing, cross-functional stakeholder coordination

## Professional Experience

### Senior Full-Stack Developer
**Fieldstone Benefits Administrators | Winnipeg, MB (Hybrid) | October 2022 – Present**

- Led migration of a legacy ASP.NET Web Forms quote engine to Angular 14 with a layered C#/Entity Framework Core service architecture, reducing quote turnaround time and cutting reported defects by roughly a third
- Introduced JWT-based authentication and a controller-service-repository pattern across the claims module, replacing session-based auth
- Built RESTful APIs in ASP.NET Core Web API against SQL Server, optimizing slow claims-lookup queries with targeted indexing and query rewrites
- Owned GitLab CI/CD pipeline for the claims platform, adding automated test gates that caught regressions before they reached staging
- Raised unit and integration test coverage on the claims module from under 40% to over 75% using xUnit and Moq, as a department-wide quality initiative

### Software Developer
**Aerotech Industries Ltd. | Winnipeg, MB (Hybrid) | September 2019 – October 2022**

- Built a real-time integration service in C#/ASP.NET Core reconciling sales lead data between the CRM and an ERP system, eliminating a recurring manual data-entry reconciliation process
- Developed a desktop-application plugin (C#, WPF) to import and validate vendor takeoff files against a custom XML schema
- Automated quality-control issue tracking with Power Apps and Power Automate, replacing a spreadsheet-based process
- Coordinated release management across environments using Azure DevOps Pipelines and a ticket-driven change process

### Programmer / Systems Analyst
**Prairie Transport Co. | Winnipeg, MB (Onsite) | May 2019 – August 2019**

- Modernized a legacy reporting application by migrating business logic into SQL Server stored procedures, improving report generation speed
- Gathered requirements and built SSRS reports for dispatch and billing teams

### .NET Developer
**Riverside Pharmacy Ltd. | Winnipeg, MB (Onsite) | November 2015 – April 2019**

- Built SSIS packages to automate a drug-data transformation process, cutting processing time from hours to well under an hour
- Owned the organization's Git source-control server (Ubuntu, SSH-administered) and led the transition off ad hoc file-share-based version control
- Migrated a legacy MS Access order-management tool to a centralized ASP.NET Web Forms application backed by SQL Server

### Software Developer
**Vantage Technology Solutions | Winnipeg, MB (Onsite) | October 2011 – March 2015**

- Developed and maintained VB.NET/C# applications against Sybase SQL Server to meet evolving client business rules
- Provided on-call production support, investigating and remediating failed overnight batch jobs under documented escalation procedures
- Built and enhanced custom reports in C# and Entity Framework against a DB2 database, working from an Agile backlog with a geographically dispersed team

## Portfolio Projects

| Project | Stack | Description | URL |
|---|---|---|---|
| ClaimsBoard | Angular · NgRx (store · effects · entity) · TypeScript · ASP.NET Core Web API · C# · .NET 8 · Entity Framework Core · SQL Server · JWT (access + refresh tokens) · Docker · Docker Compose · GitHub Actions | Sample claims-intake and triage board built as a portfolio companion to production claims-platform work. An Angular client backed by an ASP.NET Core Web API, with a full NgRx store managing claim status transitions and a Docker Compose setup wiring the API, client, and a SQL Server container together for local development. JWT access/refresh-token auth, EF Core migrations, and a GitHub Actions workflow that builds and tests both projects on every push. | https://github.com/sarah-ashford-dev/ClaimsBoard |
| PortfolioSite | HTML · Bootstrap 5 · JavaScript · CSS · GitHub Pages · GitHub Actions | Responsive static resume website. Content rendered dynamically from structured data; automatically deployed to GitHub Pages via GitHub Actions on push. | https://github.com/sarah-ashford-dev/PortfolioSite |
| job-app-copilot | Claude API · Python · python-docx · ReportLab · Markdown · GitHub | AI-assisted job application tooling: parses job descriptions, produces tailored resume/cover-letter drafts, and generates phased learning plans from a personal skills inventory. Built to explore prompt-engineering and document-generation patterns applicable to enterprise developer-productivity tooling. | https://github.com/sarah-ashford-dev/job-app-copilot |

## Key Differentiators

- Full-stack depth: ASP.NET Core + Angular in production (Fieldstone Benefits Administrators)
- CRM/ERP system integration: real-time custom API (C#/ASP.NET Core, REST, OData, JWT OAuth) integrating HubSpot, Microsoft Dynamics 365 Sales, and SharePoint Online via Dataverse and MS Graph API to resolve a production data-consistency problem; additional Dataverse/SharePoint document-library integration secured with Azure AD token-based authentication (Aerotech Industries)
- Legacy modernization: 3 separate employers, 3 migration projects
- SQL Server: 10+ years T-SQL, stored procedures, SSIS 7× improvement story, query optimization and hierarchies (course-level, Apr 2026)
- TDD: xUnit + Moq (Fieldstone Benefits Administrators), NUnit (Riverside Pharmacy)
- Linux / Unix / Shell scripting: Production Ubuntu server administration (Riverside Pharmacy), Unix shell script automation (Vantage Technology Solutions), 🟡 Portfolio-level (shell-ops-toolkit GitHub repo — Bash, Linux system administration)
- Legacy enterprise platform breadth: PowerBuilder, Sybase, and DB2 production experience spanning on-call production support, report development (DevExpress, Toad), and enterprise build/release management (TFS, InstallShield) (Vantage Technology Solutions — Lakeshore Auto Insurance Board and a provincial government client)
- GitHub Copilot: 19 courses — enterprise, CI/CD, security, AI agents
- Prompt Engineering: 6+ dedicated courses including Advanced Prompt Engineering (Intermediate, Apr 2026) + Prompt Engineering Best Practices Lab (80%+ complete, May 2026)
- AI/LLM depth: FastAPI Foundations, Introduction to Open-source LLMs, Azure Databricks for AI workloads, Introduction to Developing AI Agents (completed Jun 2026), Frameworks for Developing LLM Agents (completed Jun 2026), Domain-specific LLM Agents (completed Jun 26, 2026), Anthropic API Introduction (completed Jun 2026), Models and Parameters for Developers (completed Jun 2026), Core Concepts of Generative AI for Developers (completed Jun 2026), Vector Databases & Embeddings for Developers (completed Jul 14, 2026); Claude series: Introduction to Claude + Claude Best Practices + Prompting Basics for Claude + Claude Practical Applications + Claude Advanced Features (all completed Jun 26, 2026) — 14 AI/LLM courses total
- Communication: 19 leadership/communication Pluralsight courses
- Pace of learning: 225 courses completed + 49 in progress + 30 labs (30 completed, 0 in progress) = **304 total** since Oct 2025 *(synced from `data/pluralsight_learning_history.json`, Aug 31, 2026)*
