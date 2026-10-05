import json
import re

def analyze_project(project):
    """
    Generates structured AI analysis for a student project.
    Provides supporting evaluative intelligence across all required categories.
    """
    title = project.get('project_title', '')
    domain = project.get('domain', '')
    techs = [t.strip() for t in project.get('technologies_used', '').split(',') if t.strip()]
    tech_str = ", ".join(techs) if techs else "Not specified"
    problem = project.get('problem_statement', '')
    solution = project.get('proposed_solution', '')
    description = project.get('project_description', '')
    github_url = project.get('github_url', '')

    # Derive domain-specific insights
    domain_insights = {
        'Healthcare & MedTech': {
            'relevance': 'High critical need. Diagnostic turnaround time and remote primary care access are chronic challenges in global healthcare systems.',
            'industry_apps': 'Point-of-care emergency medical triage, remote village clinics, clinical decision support systems (CDSS), home telemetry monitors.',
            'scalability': 'Strict compliance needed for HIPAA/GDPR data security, edge quantization to minimize bandwidth, and low-latency cloud synchronization.',
            'requirements': 'ISO 13485 medical device quality standard, multi-center retrospective validation, clinical peer-review benchmark.',
            'suggested_questions': [
                "What clinical datasets or institutional ethics clearances did you utilize to validate model precision?",
                "How does the diagnostic algorithm perform on low-signal-to-noise ratio edge cases?",
                "What is your strategy for regulatory medical software clearance (e.g. FDA / CE / CDSCO)?"
            ]
        },
        'CleanTech & Sustainability': {
            'relevance': 'High commercial urgency. Stricter emissions penalties, carbon credit auditing, and environmental compliance mandate continuous monitoring.',
            'industry_apps': 'Refinery flare and pipeline monitoring, municipal waste facilities, offshore energy rigs, industrial ESG reporting platforms.',
            'scalability': 'Hardware battery endurance, ruggedized IP67 weatherproof enclosures, and LoRaWAN/mesh network telemetry over wide geographies.',
            'requirements': 'Hazardous area ATEX/IECEx explosion safety certification, periodic optical sensor calibration, fail-safe recovery.',
            'suggested_questions': [
                "What sensor recalibration intervals are required in corrosive or high-temperature ambient conditions?",
                "How does the navigation stack handle signal loss or GPS-denied environments?",
                "What are the unit manufacturing and deployment costs at commercial scale?"
            ]
        },
        'Web3 & Cybersecurity': {
            'relevance': 'Significant market pain point. Counterfeiting, supply chain opacity, and unauthorized tampering cost enterprises billions annually.',
            'industry_apps': 'Pharmaceutical cold-chain custody, luxury brand provenance, defense logistics, verified credential issuance.',
            'scalability': 'Layer-2 rollup aggregation or zero-knowledge batching to suppress on-chain gas costs beneath fractions of a cent per transaction.',
            'requirements': 'Smart contract security audits, enterprise ERP (SAP/Oracle) connectors, user-friendly keyless NFC authentication.',
            'suggested_questions': [
                "How does the architecture defend against physical tag detachment or physical cloning?",
                "What is the client-side cryptographic proof generation time on standard mobile devices?",
                "How will non-technical warehouse operators interact with the blockchain ledger?"
            ]
        },
        'AgriTech & AI': {
            'relevance': 'Substantial societal impact. Crop diseases reduce farmer yields by 20-40%; vernacular real-time agronomy advice is urgently required.',
            'industry_apps': 'Micro-crop insurance damage assessment, agricultural chemical precision spraying advisory, cooperative farmer marketplaces.',
            'scalability': 'Full offline local caching and edge inference due to spotty rural cellular connectivity, with deferred batch cloud sync.',
            'requirements': 'Extensive multi-season field testing across diverse lighting and soil conditions, multi-dialect speech synthesis.',
            'suggested_questions': [
                "How does the visual diagnostic model handle severe overexposure, shadows, or damaged camera lenses?",
                "What is your plan for localized distribution and farmer trust acquisition?",
                "How do you verify whether suggested treatments were correctly implemented?"
            ]
        }
    }

    # Match or fallback
    matched = None
    for k, v in domain_insights.items():
        if k.lower() in domain.lower() or domain.lower() in k.lower():
            matched = v
            break
    
    if not matched:
        matched = {
            'relevance': f"Directly addresses key bottlenecks within {domain}. Practical application potential observed from submitted problem statement.",
            'industry_apps': f"Enterprise workflows in {domain}, process automation, analytical telemetry, and consumer-facing digital services.",
            'scalability': 'Cloud containerization, horizontal microservice scaling, modular API contracts, and edge optimization.',
            'requirements': 'Continuous testing suites, security hardening, user feedback cycles, and performance benchmarking.',
            'suggested_questions': [
                f"How does your solution differentiate itself from existing commercial tools in {domain}?",
                "What are the primary performance bottlenecks identified during your stress tests?",
                "What technical milestones will the requested funding specifically accelerate?"
            ]
        }

    # Complexity heuristic
    tech_count = len(techs)
    has_edge_or_ml = any(t.lower() in ['pytorch', 'tensorflow', 'ros2', 'opencv', 'solidity', 'quantization', 'yolo', 'zk', 'onnx', 'c++'] for t in techs)
    if tech_count >= 5 or has_edge_or_ml:
        complexity = "High (Involves specialized algorithmic pipelines, heterogeneous tech stacks, and domain-specific hardware or cryptographic constraints)."
    elif tech_count >= 3:
        complexity = "Moderate to High (Combines structured backend services with modern client frameworks and external integration endpoints)."
    else:
        complexity = "Moderate (Standard full-stack implementation with opportunities for architectural optimization)."

    analysis = {
        "problem_relevance": matched['relevance'],
        "innovation_indicators": f"Applies {tech_str} to solve '{problem[:120]}...' with dedicated prototype logic and hackathon-validated problem formulation.",
        "technical_complexity": complexity,
        "technology_stack": techs if techs else ["Python", "Web APIs"],
        "possible_industry_applications": matched['industry_apps'],
        "scalability_considerations": matched['scalability'],
        "potential_development_requirements": matched['requirements'],
        "suggested_questions": matched['suggested_questions'],
        "github_reference": f"Target repository: {github_url}" if github_url else "No GitHub repository provided.",
        "disclaimer": "The AI analysis must only provide supporting information. The company should make the final decision."
    }

    return analysis

def chat_reply(user_message, role='student', project=None, conversation_history=None):
    """
    Role-aware, project-aware chatbot assistant.
    Strictly follows grounding and distinction rules:
    - [Student Provided Information]
    - [Extracted from Repository]
    - [AI Generated Suggestions]
    - Refuses with "I don't have enough information about this project to answer that." when facts are unknown.
    - Never hallucinates features, funding, or nonexistent repos.
    """
    msg = user_message.strip()
    msg_lower = msg.lower()

    # If project context is present, check if query relates to this specific project
    if project:
        title = project.get('project_title', 'Untitled')
        student_name = project.get('student_name', 'Student')
        college = project.get('college_name', 'N/A')
        problem = project.get('problem_statement', '')
        solution = project.get('proposed_solution', '')
        description = project.get('project_description', '')
        domain = project.get('domain', '')
        techs = project.get('technologies_used', '')
        github = project.get('github_url', '')
        demo = project.get('demo_url', '')
        docs = project.get('documentation_url', '')
        expected_funding = project.get('expected_funding', 0)
        funding_status = project.get('funding_status', 'None')
        dev_stage = project.get('development_stage', 'Planning')
        progress = project.get('progress_percentage', 0)

        # 1. Problem solved
        if any(w in msg_lower for w in ['problem', 'what problem', 'solve', 'issue']):
            return (
                f"**Based on the submitted project description:**\n\n"
                f"This project (**{title}**) aims to solve the following problem:\n"
                f"> \"{problem}\"\n\n"
                f"**Proposed Solution (Provided by Student):**\n"
                f"{solution}"
            )

        # 2. Technologies used
        if any(w in msg_lower for w in ['technolog', 'tech stack', 'languages', 'frameworks', 'tools']):
            return (
                f"**Technologies Used (Provided by Student):**\n"
                f"The project lists the following technologies: **{techs}**.\n\n"
                f"**Repository Reference:**\n"
                f"Codebase repository: {github}\n\n"
                f"**[AI Suggestion]:** "
                f"These technologies indicate a stack focused on {domain}. You can inspect specific package configurations directly in the linked repository."
            )

        # 3. Industry applications
        if any(w in msg_lower for w in ['industry', 'application', 'use in our industry', 'commercial', 'market']):
            analysis = None
            if project.get('ai_analysis_json'):
                try:
                    analysis = json.loads(project.get('ai_analysis_json'))
                except Exception:
                    pass
            if not analysis:
                analysis = analyze_project(project)
                
            return (
                f"**Based on the project description and domain ({domain}), possible applications include:**\n\n"
                f"• {analysis.get('possible_industry_applications', 'Industry workflow automation and domain optimization.')}\n\n"
                f"**[AI Suggestion]:**\n"
                f"Scalability consideration: {analysis.get('scalability_considerations', 'Standard microservice containerization.')}\n\n"
                f"*Note: These are AI-generated suggestions to assist your evaluation. The company should make the final decision.*"
            )

        # 4. Questions to ask student
        if any(w in msg_lower for w in ['question', 'ask', 'interview', 'evaluation criteria']):
            analysis = None
            if project.get('ai_analysis_json'):
                try:
                    analysis = json.loads(project.get('ai_analysis_json'))
                except Exception:
                    pass
            if not analysis:
                analysis = analyze_project(project)
            
            questions = analysis.get('suggested_questions', [
                "What is your primary milestone timeline?",
                "What technical challenges were encountered during hackathon prototyping?"
            ])
            q_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
            return (
                f"**[AI Suggested Questions for {student_name} ({title})]:**\n\n"
                f"{q_list}\n\n"
                f"*Note: These questions are generated to explore technical feasibility and milestone delivery.*"
            )

        # 5. Funding details
        if any(w in msg_lower for w in ['funding', 'budget', 'cost', 'amount', 'investment']):
            return (
                f"**Funding Information (Provided by Student):**\n\n"
                f"• Expected Funding Amount: **${expected_funding:,.2f}**\n"
                f"• Current Funding Status: **{funding_status}**\n"
                f"• Development Stage: **{dev_stage}** ({progress}% complete)\n\n"
                f"Companies can propose or adjust funding amounts directly through the Project Evaluation panel."
            )

        # 6. GitHub Repository Details
        if any(w in msg_lower for w in ['github', 'repository', 'repo', 'code', 'commit']):
            if github:
                return (
                    f"**Information Extracted from Project Submission:**\n\n"
                    f"• GitHub Repository: [{github}]({github})\n"
                    f"• Live Demo: {demo if demo else 'No live demo link provided.'}\n"
                    f"• Documentation: {docs if docs else 'Documentation link not provided.'}\n\n"
                    f"**[AI Suggestion]:** You can review commit logs, pull requests, and software licensing directly on GitHub to evaluate code quality."
                )
            else:
                return "I don't have enough information about this project to answer that. No GitHub repository was submitted."

        # 7. Development progress
        if any(w in msg_lower for w in ['progress', 'milestone', 'development', 'stage', 'status']):
            return (
                f"**Project Development Progress (System Records):**\n\n"
                f"• Submission Status: **{project.get('submission_status')}**\n"
                f"• Funding Lifecycle: **{funding_status}**\n"
                f"• Active Stage: **{dev_stage}**\n"
                f"• Completion Rate: **{progress}%**\n\n"
                f"Detailed milestones and tasks can be reviewed in the Development Dashboard."
            )

        # 8. If query is specific to features not in description or asks something unrecorded
        if any(w in msg_lower for w in ['patent', 'revenue', 'financials', 'profit', 'valuation', 'investor name', 'salary']):
            return "I don't have enough information about this project to answer that."

    # General Role-Based Assistance (when no specific project context or general inquiries)
    if role == 'student':
        # Student inquiries
        if any(w in msg_lower for w in ['how to submit', 'submit a project', 'submission']):
            return (
                "**How to Submit Your Project on Project After Life:**\n\n"
                "1. Go to your **Student Dashboard** and click **'+ Submit New Project'**.\n"
                "2. Fill in all required information:\n"
                "   • Your name, college, department & team members\n"
                "   • Hackathon where this project was originally built\n"
                "   • Clear project title & domain\n"
                "   • Problem statement (the specific challenge you address)\n"
                "   • Proposed solution & full description\n"
                "   • Technologies used (comma separated)\n"
                "   • Valid GitHub repository URL (e.g. `https://github.com/your-username/your-repo`)\n"
                "   • Live demo & documentation links (optional but recommended)\n"
                "   • Expected funding amount and contact details\n"
                "3. Click **'Submit Project'**.\n\n"
                "Your project will move to **'Submitted'** → **'Under Review'** → **'Approved'** → **'Published'** for companies to discover!"
            )

        if any(w in msg_lower for w in ['github', 'repository link', 'validate github']):
            return (
                "**GitHub Repository Guide for Students:**\n\n"
                "• **Valid Format:** Ensure your URL begins with `https://github.com/` followed by your username and repository name (e.g., `https://github.com/username/project-repo`).\n"
                "• **Public Visibility:** Make sure your repository is set to **Public** so industry reviewers can inspect your code.\n"
                "• **Essential Files:** Include a well-structured `README.md`, an open-source license (`LICENSE`), and environment setup instructions (`requirements.txt`, `package.json`, or `Dockerfile`).\n"
                "• **Commit History:** A clean commit history showing teamwork and continuous iterations builds immense trust with corporate evaluators."
            )

        if any(w in msg_lower for w in ['problem statement', 'write problem', 'improve problem']):
            return (
                "**Guide: How to Write an Impactful Problem Statement:**\n\n"
                "A strong problem statement answers 3 questions:\n"
                "1. **Who is affected?** (Target demographic or industry, e.g. *Smallholder farmers*, *Rural clinics*)\n"
                "2. **What is the exact friction or bottleneck?** (Quantify the pain: *Lack of resident cardiologists causes 4-6 hour delay*)\n"
                "3. **What is the current cost of this failure?** (*Delayed diagnosis results in high preventable mortality*)\n\n"
                "**Formula:**\n"
                "> *[Target group] currently faces [specific obstacle] resulting in [quantifiable negative outcome]. Existing solutions fail because [limitation].*\n\n"
                "Feel free to paste your draft problem statement here, and I can help refine its clarity and structure!"
            )

        if any(w in msg_lower for w in ['solution', 'explain solution', 'improve solution']):
            return (
                "**Guide: How to Explain Your Proposed Solution:**\n\n"
                "Focus on the **architecture**, **mechanism**, and **uniqueness** rather than buzzwords:\n"
                "• **Core Mechanism:** What does your system actually do step-by-step?\n"
                "• **Technical Innovation:** Why does your approach work where others fail (e.g. *quantized offline edge inference*, *tamper-proof cryptographic hashes*)?\n"
                "• **Validation:** Mention any testing, simulations, or prototypes already built during the hackathon.\n\n"
                "*Note: I can help polish your text, but technical validation is evaluated directly by reviewing companies.*"
            )

        if any(w in msg_lower for w in ['improve description', 'project description', 'refine description']):
            if len(user_message.split()) > 10:
                # The student pasted a description!
                return (
                    f"**Suggested Improvement for Your Project Description:**\n\n"
                    f"**Enhanced Draft:**\n"
                    f"> \"{user_message.strip()}\"\n\n"
                    f"**Recommendations to Enhance Clarity:**\n"
                    f"1. Highlight the quantifiable impact (e.g., latency reduction, cost reduction, accuracy percentage).\n"
                    f"2. Explicitly specify the hardware or software dependencies required to run it.\n"
                    f"3. Detail the next development milestone you will build with company funding.\n\n"
                    f"*Important: This is a writing and structural enhancement. It does not represent technical certification.*"
                )
            else:
                return (
                    "To improve your project description, paste your current draft here! I will help you structure it with clear headings:\n"
                    "• **Project Overview & Motivation**\n"
                    "• **Technical Architecture & Data Pipeline**\n"
                    "• **Current Hackathon Prototype Status**\n"
                    "• **Roadmap & Commercial Viability**"
                )

        if any(w in msg_lower for w in ['documentation', 'prepare doc', 'presentation', 'pitch deck']):
            return (
                "**Preparing Outstanding Documentation & Presentations:**\n\n"
                "• **Architecture Diagram:** Include a clean block diagram (System, Backend, Edge/Client, Database).\n"
                "• **API Contracts:** Document input/output schemas for key endpoints.\n"
                "• **Installation Guide:** Provide clear 3-step setup commands.\n"
                "• **Pitch Deck (10 slides max):** Problem → Solution → Tech Stack → Hackathon Demo Video → Team Credentials → Funding Allocation Breakdown."
            )

        if any(w in msg_lower for w in ['company question', 'respond to company', 'feedback', 'understand feedback']):
            return (
                "**Responding to Company Inquiries & Feedback:**\n\n"
                "• **Be Transparent:** If a feature is not yet built, state: *\"This is slated for Milestone 2 in our roadmap.\"* Never overpromise.\n"
                "• **Provide Evidence:** Back claims with benchmark numbers, test logs, or code snippets from your repository.\n"
                "• **Collaborative Tone:** Companies look for teams that are coachable and receptive to architectural advice.\n"
                "• **Use the Inbuilt Discussion:** Reply directly in your project's discussion thread so all parties have a permanent record."
            )

        if any(w in msg_lower for w in ['milestone', 'create milestone', 'development progress', 'tasks']):
            return (
                "**How to Create Effective Development Milestones (Module 4):**\n\n"
                "Break your project into clear, verifiable 2-3 week sprints:\n"
                "1. **Planning & Architecture:** Specifying schemas, APIs, and hardware BOM.\n"
                "2. **Prototype Refinement:** Core algorithm optimization or firmware driver completion.\n"
                "3. **Integration & Testing:** End-to-end integration, stress tests, and automated test suites.\n"
                "4. **Company Review & Pilot Deployment:** Delivering demo video, staging deployment, and audit.\n\n"
                "Navigate to the **Development Dashboard** on any funded project to add milestones and create granular sub-tasks!"
            )

        if any(w in msg_lower for w in ['funding status', 'track funding', 'payout']):
            return (
                "**Tracking Your Funding Lifecycle:**\n\n"
                "Your project moves through these explicit stages:\n"
                "`Interested` → `Shortlisted` → `Discussion` → `Funding Proposed` → `Funding Approved` → `Development Started`\n\n"
                "You can see active company offers, proposed amounts, and direct messages in your **Student Dashboard** under the 'Funding & Company Interest' tab."
            )

        # Fallback general student guidance
        return (
            "**Welcome to Project After Life Student Assistant!**\n\n"
            "I'm here to help you showcase your hackathon project to industry backers. I can assist you with:\n"
            "• **How to submit your project** & validate your GitHub link\n"
            "• **Refining your problem statement** and proposed solution\n"
            "• **Structuring project documentation** & presentation decks\n"
            "• **Preparing development milestones** and task checklists\n"
            "• **Responding to company questions** and funding offers\n\n"
            "What would you like assistance with today?"
        )

    else:
        # Company inquiries
        if any(w in msg_lower for w in ['find project', 'discover', 'browse', 'search project']):
            return (
                "**Finding & Discovering High-Potential Projects:**\n\n"
                "Navigate to the **Company Explorer** to browse all approved hackathon projects.\n"
                "You can filter by:\n"
                "• **Technology:** Python, PyTorch, ROS2, Solidity, Flutter, etc.\n"
                "• **Domain:** Healthcare, CleanTech, Web3, AgriTech, AI/ML, Robotics\n"
                "• **Hackathon Origin:** SIH, HackMIT, ETHIndia, Kavach, etc.\n"
                "• **Funding Requirement:** Custom maximum budget filter\n"
                "• **Project Status:** Under Review, Approved, Published, Development"
            )

        if any(w in msg_lower for w in ['filter', 'search by tech', 'technology']):
            return (
                "**Searching by Technology:**\n\n"
                "Use the search bar and technology dropdown in the **Company Explorer**.\n"
                "Currently featured technologies include:\n"
                "• Edge AI & ML: `PyTorch`, `TensorFlow Lite`, `OpenCV`, `YOLOv8`\n"
                "• Embedded & Robotics: `ROS2`, `Raspberry Pi`, `C++`, `LoRaWAN`\n"
                "• Web3: `Solidity`, `Polygon ZK-EVM`, `Web3.py`\n"
                "• Full-Stack: `FastAPI`, `Flask`, `React Native`, `Vue.js`"
            )

        if any(w in msg_lower for w in ['compare', 'criteria', 'evaluation']):
            return (
                "**Project Comparison & Evaluation Criteria:**\n\n"
                "When evaluating student projects, our AI analysis provides 8 key dimensions:\n"
                "1. **Problem Relevance** (Industry urgency and market size)\n"
                "2. **Innovation Indicators** (Novelty of approach vs incumbent tools)\n"
                "3. **Technical Complexity** (Algorithmic and architectural depth)\n"
                "4. **Technology Stack Suitability**\n"
                "5. **Industry Applications**\n"
                "6. **Scalability Considerations** (Edge, Cloud, or Throughput barriers)\n"
                "7. **Potential Development Requirements** (Certifications, BOM, APIs)\n"
                "8. **Tailored Interview Questions** for student founders\n\n"
                "Open any project in the **Evaluation Panel** to view the full AI analysis."
            )

        if any(w in msg_lower for w in ['funding', 'propose funding', 'approve funding', 'budget']):
            return (
                "**Funding Management for Companies:**\n\n"
                "From any project's Evaluation Page or the **Funding Dashboard**, you can:\n"
                "• **Show Interest / Shortlist** the project\n"
                "• **Request a Meeting** with the student team\n"
                "• **Request Additional Information** or benchmarks\n"
                "• **Propose Funding Amount** (milestone-tranche or lump sum)\n"
                "• **Approve or Reject Funding** with formal company notes\n\n"
                "All funding transactions and lifecycle stages (`Proposed` → `Approved` → `Development Started`) are permanently logged."
            )

        if any(w in msg_lower for w in ['monitor', 'track development', 'milestones', 'feedback']):
            return (
                "**Monitoring Project Development (Module 4):**\n\n"
                "Once funding is approved, you gain full access to the **Development Dashboard**:\n"
                "• View stage progression: `Planning` → `Prototype` → `Development` → `Testing` → `Review` → `Deployment`\n"
                "• Inspect milestone completion rates and sub-task checklists\n"
                "• Review GitHub commit updates, uploaded screenshots, and demo videos\n"
                "• Leave formal milestone feedback, approve milestones, or request changes\n"
                "• Schedule progress review meetings directly with the students"
            )

        # Fallback general company guidance
        return (
            "**Welcome to Project After Life Corporate Intelligence Assistant!**\n\n"
            "I assist industry scouts, R&D teams, and venture funds in identifying high-impact hackathon projects. I can help you with:\n"
            "• **Searching & filtering projects** by domain, tech stack, or budget\n"
            "• **Explaining technical architectures** and GitHub code implementations\n"
            "• **Synthesizing industry application opportunities**\n"
            "• **Drafting technical evaluation questions** for student founder interviews\n"
            "• **Tracking funded project milestones** and progress reports\n\n"
            "How can I assist your discovery process today?"
        )
