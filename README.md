# AortaStudiosSBEA
Aorta Studios Senior Backend Engineering Assessment: Technical Simulations

## 📋 Overview
**Deliverable:** Functional Prototype via GitHub<br />
**Expected Time:** 4-6 hours (Scenario 1) + 2-4 hours (Scenario 2 - Bonus)<br />
**Objective:** We do not test for syntax. We test for Engineering Judgment, System Architecture, and Resilience.

## 📝 Important Notes
### About This Test
This assessment reflects real-world problems our clients face. We value quality over speed. Take your time to demonstrate your best work.

### Code Ownership
All code you write belongs solely to you. We ask that you please do not share this test publicly to maintain assessment integrity.

### Questions?
If anything is unclear, make reasonable assumptions and document them in your README.

## 📦 What to Submit
Your GitHub repository should include:

### Required Files
**1. Working Code**
*   Runnable implementation of your solution
*   Tests (unit, integration, or load tests as you see fit)<br />
**2.** [**README.md**](http://README.md)
*   Instructions to run your solution locally
*   Setup requirements and dependencies
*   Any assumptions you made
*   (Optional) Documentation of load testing results or performance benchmarks<br />
**3. Architecture Documentation:** [**`architecture.md`**](http://architecture.md)<br />
This file should contain:
*   **Data Model:** Your data structures, schemas, and storage approach
*   **Concurrency Strategy:** How you handle race conditions and concurrent access
*   **Tradeoffs and Alternatives:** Design decisions you made and why you chose them over alternatives
*   **Scalability Considerations:** How your solution scales and potential bottlenecks
*   **Security Concerns & Mitigations:** Security risks you identified and how you addressed them

### Optional Submission
**Loom Video (Highly Recommended):**
*   A 5-10 minute audio/video walkthrough explaining:
    *   Your solution architecture
    *   Key technical decisions
    *   How you approached the problem
    *   Trade-offs you considered
*   This helps us understand your thought process and communication style
*   Include the Loom link in your README

## 🎯 Evaluation Criteria
Your submission will be evaluated on:
1. **Correctness (30%)** - Does your solution solve the stated problem? Does it handle edge cases?
2. **Architecture (25%)** - Code organization, design patterns, separation of concerns
3. **Scalability (20%)** - Can your solution handle the stated load? How would it scale further?
4. **Documentation (15%)** - Clarity of explanations, decision rationale, trade-off analysis
5. **Testing (10%)** - Test coverage and quality

## ⚙️ Technical Flexibility
*   Use **any programming language** you're comfortable with
*   Choose **any frameworks, databases, or tools** you prefer
*   Implement using **any architecture** you think is appropriate (monolith, microservices, serverless, etc.)
*   We want to see how **you** would solve these problems

## 🎯 The Challenge
### **REQUIRED: Complete Scenario 1**
### **BONUS: Complete Scenario 2 - Strongly Recommended**
**⭐ Important:** Candidates who complete the bonus scenario will be **strongly prioritized** and have a **significantly higher chance** of advancing to the next round. Scenario 2 demonstrates your ability to handle complex real-time systems and will set you apart from other candidates.

## 🏛️ Scenario 1: The Flash Sale Inventory
**Domain:** FinTech & E-Commerce<br />
**Focus:** ACID Compliance, Concurrency, Race Conditions<br />

### The Problem
It's Black Friday. Your e-commerce platform has ONE item left in stock. At exactly 12:00:00 PM, **10,000 users** simultaneously click "Add to Cart."
Your system must:
*   Handle this concurrent load
*   Ensure only ONE user gets the item
*   Prevent overselling (inventory never goes below zero)
*   Provide a fair experience

### The Scenario Flow
1. **Reservation Phase:** When a user adds an item to cart, it becomes "reserved" for exactly **5 minutes**
2. **Expiration:** If the user doesn't complete purchase within 5 minutes, the item returns to available inventory
3. **Purchase:** If the user completes purchase before expiration, the item is permanently removed from inventory

### Technical Requirements
Your solution must handle:<br />

**Core Functionality:**
*   Inventory reservation with automatic expiration (5-minute hold)
*   Purchase completion
*   Inventory availability checks
*   Prevention of race conditions and overselling<br />
**Edge Cases:**
*   User reserves an item but never completes purchase (item returns after 5 minutes)
*   User completes purchase at exactly the 5:00 minute mark
*   Multiple users attempting to reserve/purchase the last item simultaneously
*   System receives thousands of concurrent requests<br />
**API Design:** Provide endpoints (REST, GraphQL, gRPC - your choice) that support:
*   Reserving inventory
*   Completing a purchase
*   Checking available inventory
*   Any other operations you deem necessary<br />
**Concurrency Strategy:** Demonstrate how your locking/synchronization strategy prevents inventory from going negative under heavy load.

### What We Want to See
*   Your approach to distributed locking or concurrency control
*   How you handle time-based expiration (TTL)
*   Your strategy for preventing race conditions
*   Evidence that your solution works under load (tests, benchmarks, or load testing scripts)
*   Clear documentation of trade-offs in your approach

### Constraints
*   Start with **100 items** in inventory
*   Simulate or demonstrate handling **high concurrent load** (define "high" based on your solution)
*   Reservation period is exactly **5 minutes**

## 📡 Scenario 2: The Synchronized Classroom (BONUS)
**Domain:** EdTech & Media Streaming<br />
**Focus:** Real-Time Communication, State Synchronization, Latency Management

### The Problem
You're building a virtual classroom where students watch educational videos together. Due to varying network latencies and connection speeds, students see different video frames at any given moment.
The challenge: **Comments made at timestamp 04:30 must appear at exactly that moment for all viewers** - both live viewers and students who join later.

### The Scenario
*   **50+ students** are connected simultaneously
*   Each student's video player may be 1-10 seconds out of sync due to buffering, network latency, or pausing
*   Students post comments anchored to specific video timestamps (e.g., "Great explanation!" at 04:30)
*   When a new student joins at timestamp 02:00, they should see future comments appear at the correct timestamps as they watch
*   When a student seeks to timestamp 10:00, they should see all historical comments for timestamps 00:00-10:00

### Technical Requirements
Your solution must provide:<br />

**Core Functionality:**
*   Real-time bidirectional communication for comment delivery
*   Comment storage with precise timestamp anchoring (sub-second accuracy)
*   Synchronization logic that delivers comments at correct video timestamps regardless of network latency
*   Comment history retrieval for new viewers or those seeking through video<br />
**Edge Cases:**
*   New viewer joins mid-video and needs comment history synchronized to their playback position
*   Viewer pauses video - comments should not accumulate, but appear when they resume
*   Viewer seeks backward or forward through video
*   Network latency causes comment to arrive late (should still appear at correct timestamp)
*   Multiple comments posted at the same timestamp<br />
**API Design:** Provide a real-time communication interface and any supporting endpoints you need:
*   Connection management (joining/leaving classrooms)
*   Comment submission with timestamp
*   Comment retrieval/synchronization
*   Any other operations necessary<br />
**Synchronization Strategy:** Demonstrate how your system ensures comments appear at correct timestamps despite:
*   Variable network latency between server and clients
*   Different video playback states across clients
*   Late-joining viewers

### What We Want to See
*   Your approach to real-time bidirectional communication
*   How you handle timestamp synchronization with precision
*   Your strategy for managing state across distributed clients
*   How you handle edge cases (late arrivals, seeking, pausing)
*   Evidence of handling concurrent connections
*   Clear documentation of your synchronization algorithm

### Constraints
*   Support at least **50 concurrent viewers**
*   Comments must be anchored with **sub-second timestamp precision**
*   Message delivery should be **under 500ms** for clients with reasonable connections
*   System should handle viewers joining/leaving dynamically

### Deliverable
*   Server implementation for real-time communication and comment management
*   Data persistence layer for comment history
*   A basic client demonstration (can be simple HTML/JavaScript, CLI, or any format that shows it working)
*   Documentation of your synchronization approach

## 🚀 Bonus Points (Optional)
If you complete both scenarios and want to showcase additional skills, consider:<br />

**System Design Extras:**
*   Observability: Metrics, logging, tracing
*   Resilience: Circuit breakers, retry logic, graceful degradation
*   Security: Rate limiting, authentication, input validation
*   Deployment: Containerization, infrastructure-as-code
*   Documentation: API documentation, architecture diagrams<br />
**Advanced Features:**
*   Distributed deployment considerations
*   Database schema optimization
*   Caching strategies
*   Message queue integration
*   Monitoring dashboards

## 📬 Submission
1. Create a GitHub repository with your solution
2. Ensure your README includes clear setup instructions
3. Submit the repository link<br />
We look forward to reviewing your work. Good luck! 🎯<br />

**The Task**:
Build the WebSocket Server that orchestrates playback and comment syncing.<br />
**Technical Requirements:**
1. Server-Authoritative Time: The server must broadcast a Scheduled Timestamp (e.g., "Start playing at Server Time 10:00:05.500") to allow clients to compensate for latency.
2. Temporal Indexing: Design a data structure for storing comments that allows for $O(1)$ or $O(\\log n)$ retrieval of comments relevant to a specific video timestamp.

### 📝 Submission Guidelines
1. The Code
*   Provide a link to a Private GitHub Repo (please invite us).
*   Do not generate a full framework boilerplate (no auth, no frontend). Focus only on the logic requested.<br />
2. The Documentation ([README.md](http://README.md))<br />
Your README must include a "Design Decisions" section answering:
*   Why did you choose this specific database isolation level or locking strategy?
*   What are the trade-offs of your approach?
*   What is the Time Complexity (Big O) of your core algorithm?<br />
3. (Recommended) Video Walkthrough
*   A short video (Loom/Youtube) walking through your logic. Focus on the _why_, not the _what_.
*   Note: You do not need to be on camera; audio commentary over a screen recording is sufficient.

# 📤 Submission Process
We value clear communication as much as clean code. Please follow these steps to submit your assessment.

### 1. The Repository
*   Create a Private GitHub (or GitLab) repository.
*   Important: Do not commit your API keys. Use a `.env` file.
*   Invite our team account as a collaborator: [`info@aortastudios.com`](mailto:info@aortastudios.com)

### 2. The Explainer Video (Walkthrough)
*   Record a short (3–5 minute) screen recording (using Loom, YouTube Unlisted, or a video file).
*   What to cover:
    *   A quick demo of the system answering the test query.
    *   A brief code walkthrough highlighting your architectural choices (e.g., _"Here is why I chose Hybrid Search over pure vectors..."_).
    *   Mention which "Bonus Challenges" you attempted.
    
### 3. Final Handoff
*   Send an email to [info@aortastudios.com](mailto:info@aortastudios.com) to confirm your submission.
*   Please include:
    1. The link to your Repository.
    2. The link to your Explainer Video (or attach the file).
    3. Any additional notes or attachments (e.g., your [`DESIGN.md`](http://design.md/) if you preferred not to put it in the repo).

### 💡 Tips for the Video
*   Don't worry about high production value; a simple screen share is perfect.
*   Focus on "Why" you built it this way, not just reading the code line-by-line.
*   If something is broken, just explain why—we appreciate honesty over perfection.
