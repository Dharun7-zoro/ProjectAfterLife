# Project After Life 🚀
> **Reviving Unfunded & Unselected Hackathon Innovations for Industry Backing & Venture Launch**

Project After Life is a full-stack web platform engineered with **HTML, CSS, Python (Flask), and SQLite**. It bridges student technical teams whose projects were not selected or funded in hackathons directly with enterprise R&D scouts, venture funds, and industry evaluators.

---

## 🌟 Key Architecture & Modules

### 🎓 Module 1: Student Project Submission & Student Dashboard
- **Role-Based Authentication**: Secure registration and sign-in for students and corporate scouts.
- **17-Field Project Submission Form**:
  - Student Name, College Name, Department, Team Members, Hackathon Name.
  - Project Title, Problem Statement, Proposed Solution, Detailed Description, Domain.
  - Technologies Used, **Validated GitHub URL**, Live Demo Link, Project Documentation, Presentation Deck.
  - Expected Funding Amount ($ USD), Contact Details (Email, Phone, LinkedIn).
- **Submission Verification Lifecycle**:
  $$\text{Submitted} \longrightarrow \text{Under Review} \longrightarrow \text{Approved} \longrightarrow \text{Published}$$
- **Student Hub (Dashboard)**:
  - View & edit submitted projects.
  - Track submission verification stages.
  - Monitor corporate interest, shortlisted status, and funding proposals.
  - Direct founder-sponsor message threads.
  - Overview of active sprint development.

---

### 🔍 Module 2: Company Project Explorer & AI Analysis
- **Professional Company Explorer**:
  - Browse approved and published hackathon innovations.
  - **Multi-Faceted Search & Filters**: Search keywords, Technology Stack, Domain, Hackathon Origin, College, Maximum Funding Budget, and Project Status.
  - Rich project cards with quick GitHub links, demo links, funding requirements, and bookmarking.
- **AI-Powered Project Analysis Engine**:
  - Automatically synthesizes an objective 8-dimension analytical dossier:
    1. **Problem Relevance** (Urgency & market impact)
    2. **Innovation Indicators** (Novelty vs incumbents)
    3. **Technical Complexity** (Algorithmic & architectural depth)
    4. **Technology Stack Suitability**
    5. **Possible Industry Applications**
    6. **Scalability Considerations** (Edge, Cloud, throughput)
    7. **Potential Development Requirements** (Certifications, BOM, APIs)
    8. **Suggested Interview Questions** for founder evaluations
  - **Strict Governance Disclaimer**: *"The AI analysis must only provide supporting information. The company should make the final decision."*

---

### 💼 Module 3: Project Selection and Funding Management
- **Project Evaluation Interface**:
  - Side-by-side dossier of Student Details, Problem Statement, Solution, Tech Stack, Repositories, AI Analysis, and Private Corporate Notes.
  - **Stage-Gated Commercial Lifecycle**:
    $$\text{Interested} \longrightarrow \text{Shortlisted} \longrightarrow \text{Discussion} \longrightarrow \text{Funding Proposed} \longrightarrow \text{Funding Approved} \longrightarrow \text{Development Started}$$
  - Actions: Express Interest, Shortlist Candidate, Propose Funding Amount, Formally Approve Funding Tranche, Reject Funding, Schedule Review Meetings, and Request Information.
- **Corporate Funding Ledger (Dashboard)**:
  - Transparent records tracking: Proposed Amount, Approved Amount, Funding Date, Funding Status, and Project Stage.
  - Aggregated capital metrics: Total Deals, Proposed Capital, Committed Capital, Active Funded Startups.

---

### 🛠️ Module 4: Project Development and Progress Tracking
- **8-Stage Development Lifecycle Progression**:
  $$\text{Funding Approved} \longrightarrow \text{Planning} \longrightarrow \text{Prototype} \longrightarrow \text{Development} \longrightarrow \text{Testing} \longrightarrow \text{Company Review} \longrightarrow \text{Final Product} \longrightarrow \text{Deployment}$$
- **Dynamic Visual Progress**:
  - Real-time completion percentage dial & animated gradient progress bar.
  - Milestone cards with statuses (`Pending`, `In Progress`, `Completed`, `Approved by Company`, `Changes Requested`).
  - Interactive sub-task checklists with instant AJAX completion toggles.
- **Sponsor Auditing & Artifact Delivery**:
  - Students upload version tags, GitHub commits/branches, progress reports, screenshots, and demo videos.
  - Corporate scouts audit code, leave milestone feedback, approve deliverables, or issue change requests.
  - Automated Notifications Hub for milestone submissions, feedback, funding approvals, and meeting invites.

---

### 🤖 Inbuilt AI Chatbot Assistant
- **Universal Floating Widget**: Available on every page across the platform (`#aiChatWidgetBtn`).
- **Role Awareness**: Automatically identifies whether the user is a **Student** or **Company** and adapts tone and workflows.
- **Project-Aware Context**: Automatically binds to the current project when opened on a project page, answering queries with exact project records.
- **Fact-Grounding Rule**:
  - Clearly distinguishes between:
    - `[Student Provided Information]`
    - `[Extracted from Repository]`
    - `[AI Generated Suggestions]`
  - Strictly prevents hallucination. For unknown or speculative information:
    > *"I don't have enough information about this project to answer that."*
- **Interactive Prompt Chips**: 1-click suggested question chips tailored to the user's role and page context.

---

## ⚡ Instant Demo Credentials

The platform is pre-seeded with realistic hackathon innovations and ready-to-test accounts:

| Role | Email | Password | Pre-loaded Data |
| :--- | :--- | :--- | :--- |
| **Student** | `student@projectafterlife.io` | `password123` | **Aarav Sharma** (IIT Madras) — 2 submitted projects (*CardioLens* & *AgriPulse*), approved funding, active sprint milestones. |
| **Company Scout** | `company@projectafterlife.io` | `password123` | **TechCorp Innovations** / **HealthPulse Labs** — Active funding offers, milestone audits, saved bookmarks. |

*Quick shortcut: Click **"Demo Student"** or **"Demo Company"** in the navigation bar for instant 1-click login.*

---

## 💻 Running the Platform Locally

1. **Activate Python Environment**:
   ```bash
   python -m pip install flask werkzeug
   ```

2. **Initialize Database & Seed Data**:
   ```bash
   python database.py
   ```

3. **Start the Application**:
   ```bash
   python app.py
   ```
   Access the web interface at **`http://127.0.0.1:5000`**.
