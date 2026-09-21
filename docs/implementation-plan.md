# Implementation Plan
## Explainable AI-Powered Adaptive Learning Platform

**Version:** 1.0  
**Date:** 2026-08-13  
**Status:** Ready for Execution

---

## Overview

This document defines the phased implementation plan for the full Adaptive Learning Platform. Each phase builds on the previous and ends with a verification checkpoint.

---

## Development Phases

### PHASE 0 — Architecture & Planning ✅ (Current)

**Deliverables:**
- [x] `docs/architecture.md` — System architecture
- [x] `docs/implementation-plan.md` — This document
- [x] `docs/research-methodology.md` — Research design

---

### PHASE 1 — Project Foundation

**Goal:** Runnable skeleton with authentication, database, and CI structure.

**Tasks:**
1. Create full monorepo directory structure
2. Backend: FastAPI app skeleton (`main.py`, `config.py`, `dependencies.py`)
3. Backend: Database models (SQLAlchemy 2.0 + Alembic migrations)
4. Backend: JWT authentication (`/auth/register`, `/auth/login`, `/auth/refresh`)
5. Backend: Role-based authorization middleware
6. Backend: Structured logging setup
7. Backend: `pytest` foundation + test fixtures
8. Frontend: Vite + React + TypeScript + Tailwind CSS project
9. Frontend: Auth pages (login, register)
10. Frontend: Protected routing skeleton
11. Docker Compose: PostgreSQL + backend + frontend
12. `.env.example` with all required keys
13. Seed script with demo users (students + teachers)

**Verification:**
- [ ] `pytest` passes (auth unit tests)
- [ ] `/auth/register` and `/auth/login` return JWT
- [ ] Frontend login screen renders
- [ ] PostgreSQL migrations applied cleanly

---

### PHASE 2 — Data & Learning Analytics

**Goal:** Learner profile, event tracking, analytics engine, synthetic dataset.

**Tasks:**
1. Synthetic data generator (`data/synthetic/generator.py`)
   - 50+ students, 5+ courses, 10+ topics per course
   - Realistic mastery distributions, quiz attempts, wrong answers
   - Time-spent, retries, skip patterns
   - Multiple learning archetypes
2. Student event tracking API (`POST /events`)
3. Learning sessions API
4. Learning Analytics Engine:
   - `analytics/event_processor.py` — event ingestion
   - `analytics/feature_extractor.py` — raw → derived features
   - `analytics/mastery_calculator.py` — weighted accuracy model
   - `analytics/engagement_scorer.py` — engagement score
   - `analytics/performance_tracker.py` — trend detection
5. Learner profile builder and updater
6. `student_topic_mastery` table population pipeline
7. Jupyter notebooks: `02_dataset_exploration.ipynb`, `04_learning_analytics.ipynb`, `05_feature_engineering.ipynb`

**Verification:**
- [ ] 50+ synthetic students loaded in DB
- [ ] Event tracking API accepts events
- [ ] Mastery scores computed per student per topic
- [ ] Analytics notebook runs end-to-end

---

### PHASE 3 — Knowledge Gap Detection

**Goal:** Multi-signal gap detector with evidence, severity, and priority.

**Tasks:**
1. `knowledge_gap/signals.py` — define gap signals:
   - Low recent accuracy (< 50%)
   - Repeated mistakes (same question failed 3+)
   - Declining performance trend
   - High time-per-question on topic
   - Low mastery score (< 0.4)
   - Prerequisite not satisfied
2. `knowledge_gap/gap_scorer.py` — combine signals into gap score + severity
3. `knowledge_gap/prerequisite_checker.py` — KG-aware prerequisite traversal
4. `knowledge_gap/intervention_prioritizer.py` — rank gaps by priority
5. `knowledge_gap/detector.py` — orchestrator
6. Knowledge gaps stored in `knowledge_gaps` table
7. API: `GET /students/me/knowledge-gaps`
8. Jupyter notebook: `06_knowledge_gap_detection.ipynb`

**Verification:**
- [ ] Gap detector identifies weak topics for all 50+ synthetic students
- [ ] Prerequisite gaps are detected correctly
- [ ] Gap evidence is stored with confidence scores
- [ ] Notebook demonstrates gap detection with visualizations

---

### PHASE 4 — ML Pipeline

**Goal:** Train, compare, evaluate, and persist ML models.

**Tasks:**
1. `ml/data_loader.py` — standardized data loading interface
2. `ml/preprocessing.py` — cleaning, normalization, imputation
3. `ml/feature_engineering.py` — all engineered features (see architecture.md §5.1)
4. `ml/train.py` — training pipeline for all 4 model types
5. `ml/evaluate.py` — full metrics suite (Accuracy, F1, ROC-AUC, PR-AUC, calibration)
6. `ml/comparison.py` — model comparison table and selection
7. `ml/model_registry.py` — save model + metadata
8. `backend/app/ml/predictor.py` — inference service
9. `backend/app/ml/calibration.py` — probability calibration
10. Avoid data leakage: stratified/time-based split
11. Jupyter notebooks: `07_ml_baseline.ipynb`, `08_ml_model_comparison.ipynb`, `09_mastery_prediction.ipynb`

**Verification:**
- [ ] All 4 models trained without data leakage
- [ ] Model comparison table produced
- [ ] Best model selected with documented reasoning
- [ ] Trained models saved with versioned metadata
- [ ] Inference service returns predictions in < 100ms

---

### PHASE 5 — Adaptive Learning Engine

**Goal:** Working recommendation engine with difficulty adaptation and study plans.

**Tasks:**
1. `adaptive/engine.py` — main orchestrator
2. `adaptive/recommendation_scorer.py` — multi-factor scoring
3. `adaptive/difficulty_adapter.py` — difficulty state machine
4. `adaptive/learning_path.py` — path construction per student
5. `adaptive/study_plan_generator.py` — daily/weekly plan generator
6. `adaptive/rules.py` — configurable adaptive rules
7. APIs:
   - `GET /students/me/recommendations`
   - `GET /students/me/learning-path`
   - `GET /students/me/study-plan`
8. Recommendation stored with evidence in DB
9. Jupyter notebook: `10_adaptive_recommendation.ipynb`

**Verification:**
- [ ] Student A (Recursion gap) → Recursion recommended
- [ ] Student B (Functions gap) → Functions recommended
- [ ] Difficulty adjusts after quiz attempts
- [ ] Study plan generated with time allocations and reasons
- [ ] API returns ranked recommendations with evidence

---

### PHASE 6 — LLM Tutor Service

**Goal:** Provider-abstracted LLM tutor with personalized prompts.

**Tasks:**
1. `llm/provider.py` — AbstractLLMProvider interface
2. `llm/openai_provider.py` — OpenAI GPT-4o implementation
3. `llm/gemini_provider.py` — Gemini implementation
4. `llm/local_provider.py` — Ollama fallback
5. `llm/prompt_builder.py` — context-aware prompt assembly
6. `llm/tutor_service.py` — orchestration for explain / hint / quiz / summarize
7. `llm/quiz_generator.py` — structured JSON quiz generation + validation
8. `llm/explanation_generator.py` — personalized explanations
9. `llm/output_validator.py` — JSON schema validation, fallback
10. APIs:
    - `POST /tutor/chat`
    - `POST /tutor/explain`
    - `POST /tutor/hint`
    - `POST /tutor/generate-quiz`
    - `POST /tutor/summarize`
11. LLM conversation stored in DB
12. Graceful degradation when LLM unavailable
13. Jupyter notebooks: `13_llm_experiments.ipynb`, `14_prompt_evaluation.ipynb`

**Verification:**
- [ ] Beginner student gets simpler explanation than advanced student
- [ ] Fallback works when API key is missing
- [ ] Quiz JSON is validated before returning to client
- [ ] Tutor chat history is persisted
- [ ] Rate limiting prevents runaway LLM costs

---

### PHASE 7 — RAG Pipeline

**Goal:** Document ingestion, vector search, grounded generation with citations.

**Tasks:**
1. `rag/document_parser.py` — PDF + text parsing
2. `rag/chunker.py` — 512-token chunks, 64-token overlap
3. `rag/embedder.py` — embedding generation (OpenAI or local)
4. `rag/vector_store.py` — ChromaDB abstraction (pgvector fallback)
5. `rag/retriever.py` — similarity search + metadata filtering
6. `rag/citation_builder.py` — source references
7. `rag/pipeline.py` — end-to-end orchestration
8. Integration with LLM tutor (prefer RAG when documents available)
9. Seed with sample educational documents (CS textbook excerpts - public domain)
10. APIs:
    - `POST /documents/upload`
    - `POST /documents/index`
    - `GET /documents`
11. Jupyter notebook: `15_rag_experiments.ipynb`

**Verification:**
- [ ] PDF document ingested and chunked
- [ ] Similarity search returns relevant chunks
- [ ] LLM response includes source citations
- [ ] System signals uncertainty when no relevant context found
- [ ] No hallucinated "facts" from empty context

---

### PHASE 8 — Explainability (XAI)

**Goal:** SHAP, LIME, evidence builder, confidence estimator, human-readable explanations.

**Tasks:**
1. `explainability/shap_explainer.py` — TreeExplainer for RF/XGB
2. `explainability/lime_explainer.py` — LIME local explanations
3. `explainability/feature_importance.py` — global model explanations
4. `explainability/evidence_builder.py` — aggregate multi-signal evidence
5. `explainability/human_explainer.py` — map technical → natural language
6. `explainability/confidence_estimator.py` — weighted confidence
7. Integration: every recommendation has explanation + confidence
8. APIs:
    - `GET /recommendations/{id}/explanation`
    - `GET /students/{id}/prediction-explanation`
9. Jupyter notebooks: `11_shap_explainability.ipynb`, `12_lime_experiments.ipynb`

**Verification:**
- [ ] SHAP values computed for every prediction
- [ ] Human explanation generated for every recommendation
- [ ] Student view shows simple text explanation
- [ ] Teacher view shows detailed SHAP feature breakdown
- [ ] Confidence score correctly reflects evidence strength

---

### PHASE 9 — Knowledge Graph Integration

**Goal:** Full knowledge graph with prerequisite-aware adaptive routing.

**Tasks:**
1. `knowledge_graph/schema.py` — Node + Edge type definitions
2. `knowledge_graph/graph.py` — NetworkX graph operations
3. `knowledge_graph/traversal.py` — BFS/DFS prerequisite traversal
4. `knowledge_graph/loader.py` — load from JSON + sync to DB
5. Seed knowledge graph for demo courses
6. Integration with adaptive engine (prerequisite gating)
7. Integration with knowledge gap detector
8. APIs:
    - `GET /knowledge-graph/{course_id}`
    - `GET /topics/{topic_id}/prerequisites`
9. Jupyter notebook: `16_knowledge_graph.ipynb`

**Verification:**
- [ ] Prerequisite chain correctly traversed
- [ ] Student with Recursion gap gets Functions first (if not mastered)
- [ ] Knowledge graph renders in frontend
- [ ] Topics locked/unlocked based on prerequisite mastery

---

### PHASE 10 — Frontend Application

**Goal:** Complete student and teacher dashboards.

**Student Pages:**
1. Login / Register
2. Dashboard (mastery overview, today's plan, recommendations, streak)
3. Course Catalog
4. Course Detail + Learning Path (visual, with icons per status)
5. Topic Detail + Resources
6. AI Tutor (chat interface)
7. Quiz Interface (adaptive, timer, hints)
8. Quiz Results (score, explanations, what to study next)
9. Personalized Recommendations (with XAI cards)
10. Study Plan (daily/weekly)
11. Progress Analytics (charts)
12. Weak Topics (gap visualization)
13. Recommendation Explanations (technical + human view)
14. Profile & Settings

**Teacher Pages:**
1. Teacher Dashboard (class overview)
2. Students List (with risk indicators)
3. Student Detail (full learner profile)
4. Class Analytics (mastery heatmap, engagement trends)
5. Weak Topic Distribution
6. Knowledge Gap Overview
7. Experiment Management

**Components to Build:**
- MasteryRadarChart
- LearningPathVisualizer
- RecommendationCard (with XAI expand)
- AITutorChat
- QuizCard
- TopicMasteryBadge
- StudyPlanTimeline
- ProgressTrendChart
- GapHeatmap (teacher)
- ClassMasteryDistribution (teacher)
- ConfidenceBadge

**Verification:**
- [ ] All student pages render without errors
- [ ] All teacher pages render without errors
- [ ] Charts display real data from API
- [ ] AI tutor chat sends/receives messages
- [ ] Quiz flow works end-to-end
- [ ] Recommendation explanations expand/collapse correctly

---

### PHASE 11 — Research Experiment Framework

**Goal:** Experiment groups, pre/post testing, surveys, evaluation.

**Tasks:**
1. `experiments/manager.py` — experiment CRUD + participant assignment
2. `experiments/evaluator.py` — evaluation metric computation
3. `experiments/statistical_tests.py` — full statistical test suite
4. `experiments/ablation.py` — ablation study runner
5. Experiment group assignment (GROUP 1/2/3)
6. Pre-test / post-test / retention test management
7. Survey ingestion
8. APIs for experiment management
9. Teacher UI for experiment oversight
10. Jupyter notebooks: `17_recommendation_evaluation.ipynb`, `18_learning_outcome_evaluation.ipynb`, `19_statistical_analysis.ipynb`, `20_ablation_study.ipynb`, `21_final_research_results.ipynb`

**Verification:**
- [ ] Participants can be assigned to experiment groups
- [ ] Pre/post scores recorded
- [ ] Statistical tests run correctly on synthetic data
- [ ] Ablation framework compares all 6 system configurations
- [ ] Results do NOT fabricate or over-claim significance

---

### PHASE 12 — Full Integration

**Goal:** End-to-end feedback loop verified.

**Tasks:**
1. Verify complete loop: student event → analytics → gap → recommendation → tutor → quiz → updated mastery → new recommendation
2. Integration tests for full loop
3. Teacher dashboard shows real-time class data
4. Notebook `01_project_setup.ipynb` validates full setup

**Verification:**
- [ ] Full feedback loop works without manual intervention
- [ ] Real-time mastery updates reflected in UI
- [ ] Teacher sees updated class analytics after student activity

---

### PHASE 13 — Testing & Quality

**Goal:** Comprehensive test suite.

**Unit Tests:**
- Analytics engine functions
- Gap detector signals
- Adaptive scoring functions
- Recommendation algorithm
- Mastery calculator
- Knowledge graph traversal
- LLM output validator
- Study plan generator

**Integration Tests:**
- Analytics pipeline end-to-end
- ML training + inference pipeline
- RAG ingestion + retrieval
- Full recommendation pipeline with explanation

**API Tests (httpx + pytest):**
- Auth flow
- Student APIs
- Teacher APIs
- Quiz attempt flow
- Tutor chat flow
- Document upload + index

**Edge Case Tests:**
- Student with no history
- All topics mastered
- LLM unavailable
- Vector DB unavailable
- Empty RAG context
- Invalid quiz answer format
- Missing data in learner profile

**Verification:**
- [ ] All critical paths have tests
- [ ] Edge cases handled gracefully (no 500 errors)
- [ ] Test coverage ≥ 70% for core modules

---

### PHASE 14 — Documentation & Deployment

**Goal:** Complete documentation and Docker setup.

**Tasks:**
1. `README.md` — full project README (see Section 29 of spec)
2. `docs/database.md` — schema documentation
3. `docs/api.md` — API reference
4. `docs/ml_pipeline.md` — ML pipeline documentation
5. `docs/llm.md` — LLM setup guide
6. `docs/rag.md` — RAG setup guide
7. `docs/explainability.md` — XAI documentation
8. `docs/experiments.md` — Experiment guide
9. `docs/research-methodology.md` — Research design (see separate artifact)
10. Mermaid diagrams embedded in docs
11. `docker-compose.yml` for full stack
12. All 21 Jupyter notebooks complete and runnable

**Verification:**
- [ ] New developer can set up project from README
- [ ] Docker Compose brings up full stack
- [ ] All notebooks run from top to bottom
- [ ] No hard-coded secrets

---

## API Specification

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register student or teacher |
| POST | `/api/v1/auth/login` | Login, get JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate token |

### Student APIs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/students/me` | Current student profile |
| GET | `/api/v1/students/me/profile` | Full learner profile |
| GET | `/api/v1/students/me/mastery` | Topic mastery map |
| GET | `/api/v1/students/me/recommendations` | Ranked recommendations |
| GET | `/api/v1/students/me/study-plan` | Today's study plan |
| GET | `/api/v1/students/me/progress` | Progress history |
| GET | `/api/v1/students/me/knowledge-gaps` | Knowledge gaps |
| GET | `/api/v1/students/me/learning-path/{course_id}` | Adaptive learning path |
| POST | `/api/v1/students/me/events` | Track student event |

### Courses & Topics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/courses` | List courses |
| GET | `/api/v1/courses/{id}` | Course detail |
| GET | `/api/v1/topics/{id}` | Topic detail |
| GET | `/api/v1/topics/{id}/resources` | Topic resources |
| GET | `/api/v1/topics/{id}/prerequisites` | Prerequisite chain |

### Quizzes
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/quizzes/{id}` | Quiz detail |
| POST | `/api/v1/quizzes/{id}/attempt` | Start quiz attempt |
| POST | `/api/v1/quiz-attempts/{id}/submit` | Submit answers |
| GET | `/api/v1/quiz-attempts/{id}` | Attempt results |
| GET | `/api/v1/quiz-attempts/{id}/explanation` | Answer explanations |

### AI Tutor
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/tutor/chat` | Send chat message |
| POST | `/api/v1/tutor/explain` | Request explanation |
| POST | `/api/v1/tutor/hint` | Request hint |
| POST | `/api/v1/tutor/generate-quiz` | Generate adaptive quiz |
| POST | `/api/v1/tutor/summarize` | Generate summary |
| GET | `/api/v1/tutor/conversations` | Conversation history |

### Recommendations & XAI
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/recommendations` | Current recommendations |
| GET | `/api/v1/recommendations/{id}` | Recommendation detail |
| GET | `/api/v1/recommendations/{id}/explanation` | Full XAI explanation |
| POST | `/api/v1/recommendations/{id}/feedback` | Student feedback |

### Teacher APIs
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/teacher/dashboard` | Class overview |
| GET | `/api/v1/teacher/students` | Student list |
| GET | `/api/v1/teacher/students/{id}` | Student detail + profile |
| GET | `/api/v1/teacher/analytics/class` | Class analytics |
| GET | `/api/v1/teacher/analytics/topics` | Topic performance |
| GET | `/api/v1/teacher/knowledge-gaps` | Class-wide gaps |

### Documents (RAG)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload document |
| POST | `/api/v1/documents/{id}/index` | Index for RAG |
| GET | `/api/v1/documents` | List documents |
| DELETE | `/api/v1/documents/{id}` | Remove document |

### Knowledge Graph
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/knowledge-graph/{course_id}` | Full KG for course |
| GET | `/api/v1/knowledge-graph/node/{id}` | Node detail |

### Experiments
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/experiments` | List experiments |
| POST | `/api/v1/experiments` | Create experiment |
| GET | `/api/v1/experiments/{id}` | Experiment detail |
| GET | `/api/v1/experiments/{id}/results` | Results + metrics |
| POST | `/api/v1/experiments/{id}/participants` | Enroll participant |

---

## Frontend Page Map

### Student Application
```
/login                          → Auth: Login
/register                       → Auth: Register
/dashboard                      → Dashboard (home)
/courses                        → Course Catalog
/courses/:id                    → Course Detail
/courses/:id/learning-path      → Visual Learning Path
/topics/:id                     → Topic Detail + Resources
/tutor                          → AI Tutor Chat
/tutor/:conversationId          → Existing Conversation
/quiz/:id                       → Quiz Interface
/quiz-results/:attemptId        → Quiz Results + Explanations
/recommendations                → Recommendations + XAI
/recommendations/:id            → Single Recommendation Detail
/study-plan                     → Today's & Weekly Study Plan
/analytics                      → Progress Analytics
/analytics/weak-topics          → Weak Topic Analysis
/profile                        → Profile & Settings
```

### Teacher Application
```
/teacher/dashboard              → Class Overview
/teacher/students               → Students List
/teacher/students/:id           → Student Learner Profile
/teacher/analytics              → Class Analytics
/teacher/analytics/topics       → Topic Performance
/teacher/knowledge-gaps         → Class Knowledge Gaps
/teacher/experiments            → Experiment Management
/teacher/experiments/:id        → Experiment Results
/teacher/documents              → RAG Document Management
```

---

## Jupyter Notebook Roadmap

| Notebook | Purpose | Key Outputs |
|---|---|---|
| `01_project_setup.ipynb` | Environment check, DB connectivity, data availability | Setup validation |
| `02_dataset_exploration.ipynb` | EDA on synthetic/public dataset | Summary stats, distributions, visualizations |
| `03_data_cleaning.ipynb` | Missing values, outliers, data quality | Clean dataset |
| `04_learning_analytics.ipynb` | Feature extraction, engagement metrics | Analytics feature DataFrame |
| `05_feature_engineering.ipynb` | Derived features, correlations, importance | Feature set for ML |
| `06_knowledge_gap_detection.ipynb` | Gap detection experiments, signal analysis | Gap detection results |
| `07_ml_baseline.ipynb` | Logistic Regression baseline | Baseline metrics |
| `08_ml_model_comparison.ipynb` | RF vs XGB vs LightGBM comparison | Comparison table, ROC curves |
| `09_mastery_prediction.ipynb` | Best model, calibration, holdout evaluation | Final model metrics |
| `10_adaptive_recommendation.ipynb` | Recommendation algorithm analysis | Recommendation quality metrics |
| `11_shap_explainability.ipynb` | SHAP for best model, feature importance | SHAP plots, interpretation |
| `12_lime_experiments.ipynb` | LIME local explanations | Per-instance explanations |
| `13_llm_experiments.ipynb` | Prompt engineering, response quality | Best prompt templates |
| `14_prompt_evaluation.ipynb` | Systematic prompt evaluation | Prompt comparison table |
| `15_rag_experiments.ipynb` | Retrieval quality, context relevance | Retrieval metrics |
| `16_knowledge_graph.ipynb` | KG construction, traversal, visualization | KG visualization |
| `17_recommendation_evaluation.ipynb` | Precision@K, NDCG, relevance | Recommendation metrics |
| `18_learning_outcome_evaluation.ipynb` | Pre/post test analysis, learning gain | Learning gain analysis |
| `19_statistical_analysis.ipynb` | Group comparisons, hypothesis testing | Statistical test results |
| `20_ablation_study.ipynb` | Component ablation (6 configurations) | Ablation table |
| `21_final_research_results.ipynb` | Consolidated research results | Final report tables + plots |

---

## Ablation Study Design

| Configuration | Components Active |
|---|---|
| A: Baseline | Learning analytics only (mastery score) |
| B: Analytics + ML | A + ML prediction model |
| C: Analytics + ML + Adaptive | B + adaptive recommendation engine |
| D: Full AI | C + LLM tutor |
| E: Full + XAI | D + explainability layer |
| F: Full + XAI + RAG | E + RAG pipeline |

**Metrics compared across configurations:**
- Recommendation relevance (Precision@3)
- Learning gain (post-test - pre-test)
- User trust rating
- System response time
- Explanation quality rating

---

## Evaluation Framework

### A. Prediction Performance
- Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC
- Calibration (Brier score, reliability diagram)
- Per-topic breakdown

### B. Recommendation Quality
- Precision@K (K=3, 5)
- Recall@K
- NDCG
- User relevance ratings (from feedback table)

### C. Learning Improvement
- Normalized Learning Gain: NLG = (post - pre) / (1 - pre)
- Time to mastery per topic
- Retention score (7-day retention test)

### D. User Experience
- System Usability Scale (SUS) score
- Trust rating (Likert 1–5)
- Perceived personalization (Likert 1–5)
- Perceived usefulness (Likert 1–5)

---

## Technology Dependencies (Complete List)

### Backend (requirements.txt)
```
fastapi==0.110.0
uvicorn[standard]==0.27.0
pydantic==2.6.0
pydantic-settings==2.2.0
sqlalchemy==2.0.28
alembic==1.13.1
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
slowapi==0.1.9
scikit-learn==1.4.0
xgboost==2.0.3
lightgbm==4.3.0
shap==0.44.1
lime==0.2.0.1
networkx==3.2.1
chromadb==0.4.24
openai==1.12.0
google-generativeai==0.4.0
pandas==2.2.0
numpy==1.26.4
scipy==1.12.0
matplotlib==3.8.2
seaborn==0.13.2
pdfplumber==0.10.3
httpx==0.26.0
pytest==8.0.0
pytest-asyncio==0.23.4
```

### Frontend (package.json key deps)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "axios": "^1.6.7",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.5.0",
    "recharts": "^2.12.0",
    "react-hook-form": "^7.50.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
```
