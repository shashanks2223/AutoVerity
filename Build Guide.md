# AutoVerity

## Intelligent Media Processing Pipeline
 A complete step-by-step guide documenting how I designed, built, integrated, tested, and prepared **AutoVerity** for the Backend + AI Engineering Take-Home Assignment.

# Introduction
First, I would like to sincerely thank you for this opportunity to work on this assignment and build **AutoVerity**.
This project gave me the opportunity to go beyond simply writing code and think about how a real-world engineering system should be designed, implemented, tested, and improved. Throughout the process, I focused not only on completing the requirements but also on understanding the reasoning behind each technical decision — from asynchronous processing and database design to image analysis, API architecture, frontend integration, error handling, and testing.
I chose to document the entire development process in a **`.md` Markdown file** because Markdown allows the guide to be organized using headings, making it easy to navigate and read only the sections that are relevant.
I also used AI-assisted development tools such as **Stitch** and **Antigravity**. Rather than treating AI-generated output as automatically correct, I used these tools as engineering assistants and validated the generated work through testing, debugging, and manual review.
This document covers my complete development journey — from understanding the assignment and planning the architecture to building the frontend, implementing the backend, integrating both systems, testing the complete workflow, and preparing the final solution.
My goal was not to build an unnecessarily complicated system, but to build something **clean, practical, reliable, understandable, and honest about its limitations**.

# Project Overview

## What is AutoVerity?

**AutoVerity** is the name I chose for this project.
**Auto** → Automatic
**Verity** → Truth, accuracy, and verification
Together, **AutoVerity** represents the idea of automatically analyzing and verifying uploaded media through a structured processing pipeline.
The official assignment itself is the **Intelligent Media Processing Pipeline**, while AutoVerity is the product name I chose for my implementation.

# Step 1 — Understanding the Assignment
The first step was to understand exactly what I needed to build.
I uploaded the **Backend + AI Engineering Take-Home Assignment** to ChatGPT and asked:
"Give me a step-by-step guide of what I need to build and how I can make it unique."
Initially, ChatGPT misunderstood the assignment and framed it as a **Vehicle Image Verification & Analysis Pipeline**. However, the actual assignment is an **Intelligent Media Processing Pipeline**, with vehicle images being the problem context.
After correcting the direction, I used the assignment as the source of truth and started maintaining my development process in a **`.md` Markdown file**.

This file documents my:

* Requirements
* Architecture
* AI prompts
* Development decisions
* Problems and fixes
* Testing
* AI usage
* Final implementation

This helped me keep the entire development journey organized and traceable.

# Step 2 — Planning the System Architecture
After understanding the assignment requirements, my next step was to think about **how the complete Intelligent Media Processing Pipeline should work** before choosing specific development tools.
I broke the system into the following major components:
Frontend
   ↓
REST API
   ↓
FastAPI Backend
   ↓
Database + Job Queue
   ↓
Background Worker
   ↓
Image Analysis
   ↓
Structured Results
The main processing flow would be:
Upload Image
     ↓
Store Image + Metadata
     ↓
Generate Processing ID
     ↓
Queue Background Job
     ↓
Process Image Asynchronously
     ↓
Run Image Analysis Checks
     ↓
Store Results
     ↓
Return Status / Results

The assignment requires image processing to happen asynchronously and defines the processing states as `pending`, `processing`, `completed`, and `failed`.
At this stage, I focused on understanding the **architecture and responsibilities of each component**, rather than immediately deciding which tools to use.
Once I had a clear architecture, I could then decide which tools would help me implement each part efficiently within the 48-hour time limit.

# Step 3 — Deciding to Build a Frontend
The assignment mentions that building a UI/dashboard is **optional**, so I first considered whether I should spend time building one.
After thinking through the available options and the **48-hour time constraint**, I decided that adding a frontend would make the project more complete and demonstrate the end-to-end workflow.
For the UI, I chose **Stitch** because it could help me create a good-quality UI design quickly. This allowed me to focus more of my time on the core backend requirements, asynchronous processing, image analysis, testing, and integration.
My decision was:
> **Use Stitch for the frontend UI and Antigravity for the backend implementation.**
This was a deliberate trade-off between **development speed, UI quality, and the time available for the core engineering requirements**.
The assignment lists a dashboard/UI as a bonus area while emphasizing that engineering quality and thoughtful implementation are more important than a flashy UI.

## 📱 Mobile + 💻 Desktop Friendly
The UI is designed to be **mobile-friendly** because vehicle images are typically captured directly from a phone, eliminating the need to transfer images to another device before uploading. At the same time, it is **desktop/laptop-friendly**, allowing monitoring or verification agents to comfortably review processing status and analysis results on a larger screen.
**This ensures the system is practical for both field users and monitoring teams.**

# Step 4 — Choosing Antigravity for the Backend
After deciding to use Stitch for the frontend, I needed a development tool that could help me implement the backend while keeping the architecture and engineering decisions under my control.
I chose **Antigravity** for the backend because the project involves multiple components such as **FastAPI, PostgreSQL, Redis, Celery, image processing, OCR, APIs, and testing**.
I planned to use Antigravity to accelerate the implementation while still reviewing and validating the generated code myself.
The backend would be responsible for:
* Image upload APIs
* Metadata storage
* Asynchronous processing
* Image analysis
* OCR
* Database operations
* Processing status
* Error handling
* Testing

My overall development approach became:

Stitch
  ↓
Frontend / UI

Antigravity
  ↓
Backend / APIs / Processing

        ↓

REST API Integration
This separation allowed me to use each tool where it provided the most value while keeping the overall system architecture clear.


# Step 5 — Choosing Gemini API for AI Analysis

After planning the architecture and deciding on the development tools, I wanted to add a proper **AI analysis layer** to the pipeline.

I decided to use the **Gemini API** for image understanding because the assignment allows the use of AI APIs and encourages combining AI approaches with custom image-processing techniques.

However, I did not want Gemini to handle every check. I wanted to use the right approach for each problem.

My planned approach was:

```text
Image
  ↓
Deterministic Checks
  ├── Blur → OpenCV
  ├── Brightness → OpenCV
  ├── Dimensions → OpenCV
  └── Duplicate → Perceptual Hash
           ↓
      Gemini API
  ├── Image understanding
  ├── Vehicle/context analysis
  ├── OCR assistance
  └── Suspicious-image analysis
           ↓
    Combined Analysis
           ↓
     Structured Result
```

This gives me a **hybrid approach** where deterministic methods are used when they are more appropriate, while Gemini is used where multimodal AI can provide additional context.

The Gemini API will be called from the **backend/worker**, not directly from the frontend, so the API key remains secure.

This approach also gives me a better opportunity to evaluate the AI output rather than blindly trusting it.

## Step 6 — Designing the Image Analysis Strategy

After deciding to use Gemini, the next step was to decide **what exactly the system should analyze and which technology should handle each check**.

I wanted to avoid relying completely on AI when a simple and reliable computer-vision technique could solve the problem.

The planned checks are:

| Check                       | Approach                |
| --------------------------- | ----------------------- |
| Blur detection              | OpenCV                  |
| Brightness                  | OpenCV                  |
| Image dimensions            | OpenCV/Pillow           |
| Duplicate detection         | Perceptual hashing      |
| OCR                         | OCR + Gemini assistance |
| Vehicle number format       | Regex + OCR result      |
| Image/context analysis      | Gemini                  |
| Suspicious image indicators | Gemini + heuristics     |

The assignment requires at least **four meaningful image checks** and gives examples such as blur, brightness, duplicate detection, OCR, number-plate validation, dimensions, screenshot/photo-of-photo heuristics, and suspicious editing detection. 

My goal was to create a **hybrid analysis pipeline** where each technique is used for what it is best suited for, rather than sending every decision directly to Gemini.

```text id="d7h3xk"
                 Image
                   ↓
          Image Validation
                   ↓
       ┌───────────┴───────────┐
       ↓                       ↓
 Deterministic              Gemini
   Analysis                Analysis
       ↓                       ↓
       └───────────┬───────────┘
                   ↓
          Result Aggregation
                   ↓
          Structured Results
```

This approach also makes the system easier to debug because I can identify whether an issue came from a deterministic check, OCR, Gemini, or the result-aggregation logic.

# Step 7 — Designing the Backend Components

After deciding what the system should analyze, I planned how the backend would be structured so that each responsibility remained separate and maintainable.

I divided the backend into:

FastAPI
   │
   ├── Upload API
   ├── Status API
   ├── Results API
   └── History API
          │
          ▼
     PostgreSQL
          │
          ▼
       Redis
          │
          ▼
      Celery Worker
          │
          ▼
   Analysis Services
      ├── Blur
      ├── Brightness
      ├── Duplicate
      ├── OCR
      ├── Plate Validation
      ├── Dimensions
      └── Gemini

I wanted each analysis check to be implemented as a separate service/module rather than putting all the logic into one large function.

This would make the system easier to:

Test individual checks
Debug failures
Replace an analysis technique later
Add new checks
Maintain the code

The next step was then to define the API contracts and database structure before asking Antigravity to implement the backend.

# Step 8 — Defining the API Contracts

Before starting the implementation, I wanted to clearly define how the frontend and backend would communicate.

Since Stitch and Antigravity are developing separate parts of the system, the **REST API becomes the contract between them**.

I planned the main endpoints as:

```text
POST /api/v1/images
        ↓
Upload image and start processing

GET /api/v1/images/{id}/status
        ↓
Check processing status

GET /api/v1/images/{id}/results
        ↓
Retrieve completed analysis

GET /api/v1/images/{id}/failure
        ↓
Retrieve failure details

GET /api/v1/images
        ↓
View processing history

GET /health
        ↓
Check backend health
```

The upload API should return a **processing ID immediately**, while the actual analysis happens asynchronously in the background.

I also defined the main processing states as:

```text
pending → processing → completed
                    ↘ failed
```

Defining these contracts before implementation helps prevent frontend/backend mismatches and gives both Stitch and Antigravity a clear interface to work against.

The assignment specifically requires APIs for uploading images, checking processing status, retrieving results, and retrieving failure reasons.

# Step 9 — Designing the Database

After defining the API contracts, I planned how the uploaded images, processing status, metadata, and analysis results would be stored.

The assignment requires database persistence and recommends PostgreSQL, MySQL, or MongoDB. I decided to use **PostgreSQL** because the data has a clear relational structure and I wanted reliable status tracking and structured persistence.

The main entities I planned were:

```text id="m3j6br"
Image / Processing Job
        │
        └── Analysis Result
```

### Processing Job

Stores information such as:

* Processing ID
* Original filename
* Stored filename
* File type
* File size
* File path
* Processing status
* Image hash
* Created/updated timestamps
* Failure reason

### Analysis Result

Stores the structured output from the image-analysis pipeline, including:

* Blur analysis
* Brightness analysis
* Duplicate detection
* OCR result
* Vehicle number validation
* Image dimensions
* Gemini analysis
* Overall assessment

I also planned to keep the processing record separate from the analysis result so that the **job lifecycle and analysis data have clear responsibilities**.

The next step was to take these requirements and give Antigravity a detailed implementation prompt rather than asking it to build the backend blindly.

