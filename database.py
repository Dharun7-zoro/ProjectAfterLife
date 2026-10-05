import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_after_life.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'company', 'admin')),
        organization TEXT,
        department TEXT,
        contact_phone TEXT,
        avatar_url TEXT,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Projects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        college_name TEXT NOT NULL,
        department TEXT NOT NULL,
        team_members TEXT,
        hackathon_name TEXT NOT NULL,
        project_title TEXT NOT NULL,
        problem_statement TEXT NOT NULL,
        proposed_solution TEXT NOT NULL,
        project_description TEXT NOT NULL,
        domain TEXT NOT NULL,
        technologies_used TEXT NOT NULL,
        github_url TEXT NOT NULL,
        demo_url TEXT,
        documentation_url TEXT,
        presentation_url TEXT,
        expected_funding REAL NOT NULL DEFAULT 0.0,
        contact_details TEXT NOT NULL,
        
        -- Module 1 Lifecycle: Submitted -> Under Review -> Approved -> Published
        submission_status TEXT NOT NULL DEFAULT 'Submitted',
        
        -- Module 3 Lifecycle: Interested -> Shortlisted -> Discussion -> Funding Proposed -> Funding Approved -> Development Started
        funding_status TEXT NOT NULL DEFAULT 'None',
        
        -- Module 4 Lifecycle: Funding Approved -> Planning -> Prototype -> Development -> Testing -> Company Review -> Final Product -> Deployment
        development_stage TEXT DEFAULT 'Planning',
        progress_percentage INTEGER DEFAULT 0,
        
        ai_analysis_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Company Project Interactions / Funding Records (Module 3)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        company_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Interested', 'Shortlisted', 'Discussion', 'Funding Proposed', 'Funding Approved', 'Rejected')),
        proposed_amount REAL DEFAULT 0.0,
        approved_amount REAL DEFAULT 0.0,
        funding_date TIMESTAMP,
        company_notes TEXT,
        meeting_requested INTEGER DEFAULT 0,
        meeting_details TEXT,
        additional_info_requested INTEGER DEFAULT 0,
        additional_info_query TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Messages / Discussions between Student and Company
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        sender_name TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        recipient_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Milestones (Module 4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        target_date TEXT,
        stage TEXT NOT NULL DEFAULT 'Planning',
        status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Approved by Company', 'Changes Requested')),
        company_feedback TEXT,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')

    # Tasks within Milestones (Module 4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        is_completed INTEGER DEFAULT 0,
        assigned_to TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (milestone_id) REFERENCES milestones (id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')

    # Progress Updates & Artifacts (Module 4)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        version_tag TEXT NOT NULL,
        github_commit_or_branch TEXT,
        report_text TEXT NOT NULL,
        screenshot_urls TEXT,
        demo_video_url TEXT,
        company_feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')

    # Notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_id INTEGER,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Saved / Bookmarked Projects by Companies
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS saved_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(company_id, project_id),
        FOREIGN KEY (company_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

def seed_sample_data():
    """Populates realistic seed data for instant evaluation and demonstration."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        return

    # Seed Demo Users
    demo_password = generate_password_hash("password123")
    
    users = [
        # Students
        (1, "Aarav Sharma", "student@projectafterlife.io", demo_password, "student", "IIT Madras", "Computer Science & Engineering", "+91 98765 43210", "Final year CS student passionate about Edge AI and Healthcare IoT."),
        (2, "Priya Patel", "priya@projectafterlife.io", demo_password, "student", "BITS Pilani", "Electronics & Instrumentation", "+91 98451 12345", "Hardware & embedded robotics developer. Smart mobility researcher."),
        (3, "Rohan Verma", "rohan@projectafterlife.io", demo_password, "student", "NIT Trichy", "Information Technology", "+91 97890 87654", "Full-stack Web3 & distributed systems builder."),
        
        # Companies
        (4, "TechCorp Ventures", "company@projectafterlife.io", demo_password, "company", "TechCorp Innovations Ltd.", "Corporate Venture & R&D", "+1 415 555 0199", "Enterprise venture arm investing in deep-tech, AI, and green energy innovations."),
        (5, "HealthPulse Labs", "healthpulse@projectafterlife.io", demo_password, "company", "HealthPulse Technologies", "Healthcare Innovation & Medical Devices", "+1 617 555 0144", "Pioneering AI-driven diagnostic solutions and portable clinical telemetry."),
        (6, "Nexus Mobility & CleanTech", "nexus@projectafterlife.io", demo_password, "company", "Nexus Mobility Group", "Electric Mobility & Energy", "+1 206 555 0188", "Accelerating next-generation battery management and autonomous vehicle systems.")
    ]

    for u in users:
        cursor.execute('''
        INSERT INTO users (id, name, email, password_hash, role, organization, department, contact_phone, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', u)

    # Seed Projects
    # Project 1: CardioLens AI (Approved & Published, Funded, Development Stage: Development)
    p1_ai = {
        "problem_relevance": "High. Cardiovascular diseases remain the #1 global cause of mortality; rural clinics lack certified cardiologists for immediate ECG interpretation.",
        "innovation_indicators": "Ultra-lightweight 1D-CNN quantized for $15 Raspberry Pi Zero devices, achieving 97.4% arrhythmia classification accuracy offline.",
        "technical_complexity": "High (Edge-optimized deep learning inference, real-time noise reduction DSP filter, Bluetooth Low Energy sync protocol).",
        "technology_stack": ["Python", "PyTorch Mobile", "FastAPI", "TensorFlow Lite", "Raspberry Pi", "React Native", "SQLite"],
        "possible_industry_applications": "Portable ambulance triage kits, remote village tele-medicine pods, home cardiac rehabilitation wearable integration.",
        "scalability_considerations": "Requires cloud federated learning for continuous multi-hospital model calibration while preserving patient HIPAA/GDPR privacy.",
        "potential_development_requirements": "ISO 13485 clinical software compliance, multi-lead hardware amplifier shielding against ambient 50Hz hum, rigorous multi-center clinical validation.",
        "suggested_questions": [
            "How do you handle ECG baseline drift and motion artifacts during active patient movement?",
            "What is the inference latency and battery drain on the Raspberry Pi Zero?",
            "Are there plans for regulatory CE/FDA software certification pathways?"
        ],
        "disclaimer": "This analysis provides supporting exploratory data to assist evaluation. Final investment and technical decisions remain strictly with the evaluating company."
    }

    # Project 2: AeroSense Drone CleanTech (Published, Funding Proposed)
    p2_ai = {
        "problem_relevance": "Critical. Industrial flare stacks and pipeline methane emissions cause immense greenhouse warming and severe safety penalties.",
        "innovation_indicators": "Multispectral optical gas imaging fused with autonomous quadcopter trajectory planning and hyper-local plume dispersion modeling.",
        "technical_complexity": "High (Computer vision plume segmentation, ROS2 autonomous flight, micro-LiDAR obstacle avoidance, LoRaWAN telemetry).",
        "technology_stack": ["Python", "ROS2", "OpenCV", "YOLOv8", "FastAPI", "Docker", "LoRaWAN", "Vue.js"],
        "possible_industry_applications": "Refinery safety audits, municipal landfill methane tracking, offshore gas rig leak prevention.",
        "scalability_considerations": "Drone battery life limits mission duration to 35 minutes; automated battery-swapping station design needed.",
        "potential_development_requirements": "Explosion-proof ATEX drone chassis certification for hazardous Zone 1 industrial areas.",
        "suggested_questions": [
            "What sensor calibration frequency is required for sulfur and methane parts-per-million optical detectors?",
            "How does the navigation stack handle GNSS-denied environments underneath industrial steel pipes?"
        ],
        "disclaimer": "This analysis provides supporting exploratory data to assist evaluation. Final investment and technical decisions remain strictly with the evaluating company."
    }

    # Project 3: ZeroTrust Ledger (Approved & Published, Under Discussion)
    p3_ai = {
        "problem_relevance": "Moderate to High. Counterfeit pharmaceutical distribution in developing nations causes over 100,000 preventable deaths annually.",
        "innovation_indicators": "Tamper-evident NFC cryptographic signatures married with lightweight Polygon zero-knowledge rollups for batch traceability.",
        "technical_complexity": "Moderate-High (Solidity smart contracts, Zero Knowledge proofs via SnarkJS, mobile NFC reading, IPFS metadata store).",
        "technology_stack": ["Solidity", "Python", "Ethers.js", "Web3.py", "FastAPI", "Polygon ZK-EVM", "React"],
        "possible_industry_applications": "Pharmaceutical cold-chain logistics, luxury goods anti-counterfeiting, defense spare parts validation.",
        "scalability_considerations": "Gas fees require layer-2 rollup batching to keep per-item verification cost below $0.005.",
        "potential_development_requirements": "Integration with existing enterprise ERPs (SAP/Oracle SCM) and GS1 barcodes standards.",
        "suggested_questions": [
            "What happens if a physical NFC tag is cloned or removed from the medicine vial?",
            "How quickly can a pharmacy technician verify a batch of 500 boxes at the dock?"
        ],
        "disclaimer": "This analysis provides supporting exploratory data to assist evaluation. Final investment and technical decisions remain strictly with the evaluating company."
    }

    # Project 4: AgriPulse AI (Submitted / Under Review by Student Aarav)
    p4_ai = {
        "problem_relevance": "High. Smallholder farmers lose up to 40% of crop yields to fungal blight due to delayed diagnosis and pesticide misapplication.",
        "innovation_indicators": "Smartphone camera offline leaf pathology detection using quantized Vision Transformers with regional dialect voice assistance.",
        "technical_complexity": "Moderate (MobileNetV3 quantized model, Hindi/Tamil speech-to-text, weather API microservice).",
        "technology_stack": ["Python", "Flask", "TensorFlow Lite", "Flutter", "SQLite", "OpenWeatherMap API"],
        "possible_industry_applications": "Agri-chemical advisory apps, micro-crop insurance verification, cooperative farming portals.",
        "scalability_considerations": "Offline functionality is strong; server synchronization needed when intermittent 4G connects.",
        "potential_development_requirements": "Expanding dataset to 25 additional regional Indian crops and multi-language audio synthesis.",
        "suggested_questions": [
            "What is your model's accuracy on low-resolution smartphone cameras under intense sunlight?",
            "How do you plan to partner with local agricultural extension offices?"
        ],
        "disclaimer": "This analysis provides supporting exploratory data to assist evaluation. Final investment and technical decisions remain strictly with the evaluating company."
    }

    projects = [
        (
            1, 1, "Aarav Sharma", "IIT Madras", "Computer Science & Engineering",
            "Aarav Sharma (Lead), Neha Sen (ML), Vikram Raj (Firmware)",
            "Smart India Hackathon 2025",
            "CardioLens: Portable Edge AI Arrhythmia Diagnostic Suite",
            "Rural medical sub-centers lack resident cardiologists, causing critical 4-6 hour delays in identifying acute cardiac events from raw 12-lead ECGs.",
            "A $15 handheld Edge-AI device that takes multi-channel analog ECG leads, runs an offline quantized CNN inference within 1.2 seconds, and warns local nurses of life-threatening arrhythmias.",
            "CardioLens bridges the diagnostic gap in underserved rural clinics. While we were runners-up at SIH 2025, our working hardware prototype was praised for its instant edge inference. We have gathered over 20,000 annotated PhysioNet samples and built a functioning BLE gateway to transmit emergency telemetry to district hospitals.",
            "Healthcare & MedTech",
            "Python, PyTorch Mobile, FastAPI, TensorFlow Lite, C++, Raspberry Pi, React Native",
            "https://github.com/aarav-sharma-med/cardiolens-edge",
            "https://cardiolens-demo.projectafterlife.io",
            "https://docs.cardiolens.io/v1-architecture",
            "https://slides.cardiolens.io/sih-deck.pdf",
            12000.0,
            "aarav.sharma@alumni.iitm.ac.in | +91 98765 43210 | linkedin.com/in/aarav-medtech",
            "Published",
            "Funding Approved",
            "Development",
            65,
            json.dumps(p1_ai)
        ),
        (
            2, 2, "Priya Patel", "BITS Pilani", "Electronics & Instrumentation",
            "Priya Patel (Hardware Lead), Siddharth Joshi (Robotics), Aman Khan (CV)",
            "HackMIT Global 2025",
            "AeroSense: Autonomous Methane & Emission Triage Drone",
            "Fugitive methane leaks and pipeline flares cause severe environmental degradation and fire hazards, costing oil & gas operators millions in regulatory fines.",
            "An autonomous aerial quadcopter equipped with low-cost infrared optical gas sensors and edge-computed plume segmentation to pinpoint sub-surface gas leaks with sub-meter GPS accuracy.",
            "Developed during HackMIT 2025 where time ran out before final flight testing. Since then, our team has completed the ROS2 flight controller, trained a YOLOv8 plume tracker, and proven 91% detection on simulated pipeline leaks in a controlled wind tunnel.",
            "CleanTech & Sustainability",
            "Python, ROS2, OpenCV, YOLOv8, LoRaWAN, FastAPI, Docker, Vue.js",
            "https://github.com/priyapatel-tech/aerosense-drone",
            "https://aerosense-telemetry.projectafterlife.io",
            "https://aerosense.io/whitepaper.pdf",
            "https://slideshare.net/aerosense-hackmit",
            18500.0,
            "priya.patel@pilani.bits-pilani.ac.in | +91 98451 12345",
            "Published",
            "Funding Proposed",
            "Planning",
            20,
            json.dumps(p2_ai)
        ),
        (
            3, 3, "Rohan Verma", "NIT Trichy", "Information Technology",
            "Rohan Verma (Smart Contracts), Kavya Nair (Frontend)",
            "ETHIndia 2025",
            "PharmaTrace Zero: Anti-Counterfeit Pharmaceutical Ledger",
            "Counterfeit pharmaceutical medicines infiltrate supply chains across tier-2/3 cities, causing fatal treatment failures and zero manufacturer accountability.",
            "Tamper-proof NFC tags paired with instant Polygon zero-knowledge rollups, allowing consumers and pharmacists to verify drug authenticity via any NFC phone without revealing proprietary batch sizes.",
            "Built for ETHIndia 2025. Although our hackathon pitch was eliminated in the finals due to Wi-Fi drops on stage, the entire cryptographic protocol and smart contracts are fully audited and functional on testnet.",
            "Web3 & Cybersecurity",
            "Solidity, Python, Web3.py, SnarkJS, Polygon ZK-EVM, FastAPI, React",
            "https://github.com/rohan-verma-dev/pharmatrace-zk",
            "https://pharmatrace-zk.projectafterlife.io",
            "https://github.com/rohan-verma-dev/pharmatrace-zk/wiki",
            "https://pitch.com/pharmatrace-deck",
            8500.0,
            "rohan.verma@nitt.edu | +91 97890 87654",
            "Published",
            "Discussion",
            "Planning",
            10,
            json.dumps(p3_ai)
        ),
        (
            4, 1, "Aarav Sharma", "IIT Madras", "Computer Science & Engineering",
            "Aarav Sharma, Deepa Ramesh",
            "Kavach Hackathon 2025",
            "AgriPulse: Multilingual Edge AI Crop Blight Sentinel",
            "Marginalized farmers incur catastrophic crop losses due to late diagnosis of leaf blight and lack of vernacular agronomy advice.",
            "Offline mobile smartphone application leveraging lightweight vision transformers to diagnose 38 crop diseases and deliver vernacular voice guidance in 6 regional languages.",
            "Created during Kavach Hackathon. Submitted prototype with 94.2% top-1 accuracy on tomato and potato blight datasets.",
            "AgriTech & AI",
            "Python, TensorFlow Lite, Flutter, FastAPI, SQLite",
            "https://github.com/aarav-sharma-med/agripulse-edge-ai",
            "https://agripulse.projectafterlife.io",
            "https://github.com/aarav-sharma-med/agripulse-edge-ai/blob/main/README.md",
            "",
            6000.0,
            "aarav.sharma@alumni.iitm.ac.in | +91 98765 43210",
            "Under Review",
            "None",
            "Planning",
            0,
            json.dumps(p4_ai)
        )
    ]

    for p in projects:
        cursor.execute('''
        INSERT INTO projects (
            id, student_id, student_name, college_name, department, team_members,
            hackathon_name, project_title, problem_statement, proposed_solution,
            project_description, domain, technologies_used, github_url, demo_url,
            documentation_url, presentation_url, expected_funding, contact_details,
            submission_status, funding_status, development_stage, progress_percentage, ai_analysis_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)

    # Seed Project Interest & Funding for Project 1 (CardioLens with HealthPulse Labs)
    cursor.execute('''
    INSERT INTO project_interests (
        project_id, company_id, status, proposed_amount, approved_amount,
        funding_date, company_notes, meeting_requested, meeting_details
    ) VALUES (
        1, 5, 'Funding Approved', 12000.0, 12000.0,
        CURRENT_TIMESTAMP,
        'Outstanding edge AI application. The team demonstrated clear signal filtering algorithms and reproducible benchmarks on real Raspberry Pi hardware. Approved seed funding tranche 1.',
        1, 'Initial technical review meeting completed on Zoom. Next sprint checkpoint set for end of month.'
    )
    ''')

    # Seed Project Interest for Project 2 (AeroSense with Nexus Mobility)
    cursor.execute('''
    INSERT INTO project_interests (
        project_id, company_id, status, proposed_amount, approved_amount,
        funding_date, company_notes, meeting_requested, meeting_details
    ) VALUES (
        2, 6, 'Funding Proposed', 18500.0, 0.0,
        CURRENT_TIMESTAMP,
        'High commercial potential for industrial refinery emission monitoring. Proposed $18,500 milestone-based tranche pending ATEX safety enclosure review.',
        1, 'Virtual briefing scheduled for next Thursday at 3:00 PM EST.'
    )
    ''')

    # Seed Project Interest for Project 3 (ZeroTrust with TechCorp Ventures)
    cursor.execute('''
    INSERT INTO project_interests (
        project_id, company_id, status, proposed_amount, approved_amount,
        funding_date, company_notes, meeting_requested, meeting_details
    ) VALUES (
        3, 4, 'Discussion', 0.0, 0.0,
        NULL,
        'Innovative ZK rollup application for supply chain authenticity. Requesting benchmark metrics comparing SnarkJS proof generation latency on mobile devices.',
        0, ''
    )
    ''')

    # Seed Messages between HealthPulse Labs (Company ID 5) and Aarav Sharma (Student ID 1) for Project 1
    cursor.execute('''
    INSERT INTO messages (project_id, sender_id, sender_name, sender_role, recipient_id, message, is_read)
    VALUES 
    (1, 5, 'Dr. Marcus Vance (HealthPulse Labs)', 'company', 1, 'Hello Aarav, we thoroughly reviewed your SIH 2025 presentation on CardioLens. The 1D-CNN architecture looks remarkably resilient against noise. We are approving your $12,000 funding milestone proposal.', 1),
    (1, 1, 'Aarav Sharma', 'student', 5, 'Thank you Dr. Vance! We are thrilled to partner with HealthPulse Labs. We have already initiated Sprint 2: 12-lead hardware analog shield calibration.', 1),
    (1, 5, 'Dr. Marcus Vance (HealthPulse Labs)', 'company', 1, 'Splendid. Please keep the milestone dashboard updated with test telemetry so our biomedical engineers can review.', 0)
    ''')

    # Seed Milestones for Project 1 (CardioLens)
    milestones_p1 = [
        (1, 1, "Milestone 1: DSP Baseline Wandering Filter & Noise Reduction", "Implement bandpass FIR filter (0.5Hz - 45Hz) to strip 50Hz electrical hum and patient movement baseline drift.", "2026-10-15", "Planning", "Approved by Company", "Filter coefficients verified. 99.1% SNR improvement confirmed on simulated noise runs.", datetime.now().isoformat()),
        (2, 1, "Milestone 2: 1D-CNN Quantization for Raspberry Pi Zero", "Quantize 1D-CNN to 8-bit INT8 weights using TensorFlow Lite; achieve under 1500ms latency per 10-second ECG strip.", "2026-10-30", "Prototype", "Approved by Company", "Inference benchmark achieved 1180ms with negligible loss in F1 score (0.972).", datetime.now().isoformat()),
        (3, 1, "Milestone 3: Hardware BLE Firmware & Bluetooth Sync Protocol", "Develop Nordic nRF52 BLE firmware to stream real-time telemetry to Android/iOS companion application.", "2026-11-20", "Development", "In Progress", "Currently drafting packet framing protocol to prevent dropouts during patient transport.", None),
        (4, 1, "Milestone 4: Clinical Benchmarking & Multi-lead Validation", "Test on 500 anonymized multi-lead hospital records and prepare ISO 13485 design dossier.", "2026-12-15", "Testing", "Pending", "", None)
    ]

    for m in milestones_p1:
        cursor.execute('''
        INSERT INTO milestones (id, project_id, title, description, target_date, stage, status, company_feedback, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', m)

    # Seed Tasks for Milestone 1, 2, 3
    tasks_p1 = [
        (1, 1, "Design 4th-order Butterworth digital filter in Python SciPy", 1, "Aarav Sharma"),
        (2, 1, "Port filter logic to C++ for embedded microcontrollers", 1, "Vikram Raj"),
        (3, 1, "Validate noise rejection on MIT-BIH Arrhythmia synthetic dataset", 1, "Neha Sen"),
        
        (2, 2, "Convert PyTorch model graph to ONNX representation", 1, "Neha Sen"),
        (2, 2, "Run INT8 post-training quantization on representative dataset", 1, "Neha Sen"),
        (2, 2, "Measure thermal throttling and RAM footprint on Pi Zero", 1, "Vikram Raj"),
        
        (3, 3, "Implement BLE GATT custom cardiac service profile", 1, "Vikram Raj"),
        (3, 3, "Stress test 4-hour continuous streaming with zero packet loss", 0, "Aarav Sharma"),
        (3, 3, "Implement automatic Bluetooth reconnect & local flash cache", 0, "Vikram Raj")
    ]

    for t in tasks_p1:
        cursor.execute('''
        INSERT INTO tasks (milestone_id, project_id, title, is_completed, assigned_to)
        VALUES (?, ?, ?, ?, ?)
        ''', t)

    # Seed Progress Updates for Project 1
    cursor.execute('''
    INSERT INTO progress_updates (project_id, version_tag, github_commit_or_branch, report_text, screenshot_urls, demo_video_url, company_feedback)
    VALUES (
        1, 'v0.3.1-alpha', 'feature/int8-quantization-benchmarks',
        'Sprint 2 complete! Successfully reduced model weight size from 44MB to 4.2MB using INT8 dynamic range quantization. Real-time inference on the Pi Zero is down to 1180ms per strip without loss of sensitivity on ventricular tachycardia waveforms.',
        '["https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&auto=format&fit=crop&q=60", "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=800&auto=format&fit=crop&q=60"]',
        'https://youtu.be/demo-cardiolens-v2',
        'Remarkable engineering work by Aarav and team. Memory overhead looks well within acceptable safety boundaries.'
    )
    ''')

    # Seed Notifications for Aarav Sharma (Student ID 1)
    notifications = [
        (1, 1, 'funding_updates', 'Funding Approved by HealthPulse Labs', 'HealthPulse Labs has approved your $12,000 project funding proposal for CardioLens!'),
        (1, 1, 'company_feedback', 'New Milestone Feedback', 'Dr. Marcus Vance left feedback on Milestone 2: INT8 Quantization.'),
        (1, 1, 'company_interest', 'New Company Interest', 'TechCorp Ventures viewed your project profile.'),
        (5, 1, 'milestone_completed', 'Milestone Completed: INT8 Quantization', 'Aarav Sharma submitted Milestone 2 for your review.')
    ]

    for n in notifications:
        cursor.execute('''
        INSERT INTO notifications (user_id, project_id, type, title, message)
        VALUES (?, ?, ?, ?, ?)
        ''', n)

    # Seed Saved Project for Company 4 (TechCorp Ventures saves Project 1 and 2)
    cursor.execute("INSERT INTO saved_projects (company_id, project_id) VALUES (4, 1)")
    cursor.execute("INSERT INTO saved_projects (company_id, project_id) VALUES (4, 2)")
    cursor.execute("INSERT INTO saved_projects (company_id, project_id) VALUES (5, 1)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_sample_data()
    print("Database initialized and populated successfully.")
