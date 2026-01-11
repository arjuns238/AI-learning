# Expert Review Platform Specification

## Purpose

A platform where experts (you + collaborators) can:
1. Review AI-generated pedagogical intent
2. Approve, edit, or reject outputs
3. Provide structured feedback that becomes training data
4. Track quality metrics over time

## Phase 1: Airtable/Sheets (Week 1-2)

**Why start here:**
- Validate workflow before building
- Learn what reviewers actually need
- Get first 20-50 reviews done quickly

**Setup:**
```
1. Create Airtable base with 3 tables (see below)
2. Upload generated outputs as records
3. Create review form view
4. Invite 2-3 expert reviewers
5. Export approved examples to data/training/
```

### Airtable Schema

**Table: Generated Outputs**
- id (auto)
- topic (text)
- domain (select: ML, math, physics, CS)
- difficulty_level (1-5)
- core_question (long text)
- target_mental_model (long text)
- common_misconception (long text)
- disambiguating_contrast (long text)
- concrete_anchor (long text)
- check_for_understanding (long text)
- spatial_metaphor (text, optional)
- generation_timestamp (datetime)
- model_used (text)
- exemplar_ids (text)
- status (select: pending, approved, needs_revision, rejected)

**Table: Expert Reviews**
- id (auto)
- output_id (link to Generated Outputs)
- reviewer_name (text)
- review_timestamp (datetime)
- overall_rating (1-5)
- decision (select: approve, minor_edit, major_revision, reject)
- pedagogical_accuracy (1-5)
- misconception_relevance (1-5)
- contrast_effectiveness (1-5)
- concreteness (1-5)
- assessment_validity (1-5)
- edited_fields (checkbox: core_question, mental_model, ...)
- revision_notes (long text)
- time_spent_minutes (number)

**Table: Training Data**
- Linked view of approved outputs
- Export as JSON for fine-tuning

**Workflow:**
1. Generator outputs → Upload to "Generated Outputs"
2. Reviewer opens form view → Reviews each field
3. Makes edits inline or in revision_notes
4. Submits review
5. Approved items → Auto-link to "Training Data"

## Phase 2: Custom Web Platform (Month 2-3)

Once you've done 50+ reviews and understand the workflow, build custom.

### Tech Stack Recommendation

**Backend:**
- FastAPI (Python, matches your stack)
- PostgreSQL (stores outputs + reviews)
- Pydantic models (reuse layer1/schema.py!)

**Frontend:**
- React or Next.js
- TailwindCSS for styling
- Simple, focused UI

**Hosting:**
- Vercel/Railway/Render (easy deployment)
- Supabase (managed Postgres + auth)

### Core Features

#### 1. Review Queue
```
/review
- Shows next pedagogical output to review
- Clean, focused interface
- Side-by-side: Generated vs Your Edits
- Keyboard shortcuts for speed
```

**UI mockup:**
```
┌─────────────────────────────────────────────────────┐
│ Review Queue (5 pending)          [Skip] [Save]     │
├─────────────────────────────────────────────────────┤
│ Topic: Backpropagation in Neural Networks           │
│ Domain: Machine Learning | Difficulty: 3/5          │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Core Question:                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ How does the network figure out which weights   │ │
│ │ caused the error?                                │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Rating: ○ ○ ○ ● ○  (4/5)  [✓ Approve] [Edit]       │
│                                                      │
│ Target Mental Model:                                 │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Editable text area with diff highlighting]     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Rating: ○ ○ ○ ○ ●  (5/5)  [✓ Approve] [Edit]       │
│                                                      │
│ [Similar for all 6 fields...]                       │
│                                                      │
├─────────────────────────────────────────────────────┤
│ Overall Decision:                                    │
│ ○ Approve  ○ Minor Edit  ○ Major Revision  ○ Reject│
│                                                      │
│ Notes:                                               │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Optional comments...                             │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│         [Previous] [Skip] [Submit Review]           │
└─────────────────────────────────────────────────────┘
```

#### 2. Dashboard

```
/dashboard
- Total generations: 127
- Pending review: 23
- Approval rate: 78%
- Average quality score: 3.8/5

Charts:
- Approval rate over time (trending up/down?)
- Quality by domain (ML: 4.2, Math: 3.5, etc.)
- Common failure modes (misconceptions too vague: 15%)
- Reviewer agreement (inter-rater reliability)
```

#### 3. Training Data Export

```
/training-data
- Filter approved outputs
- Export formats:
  - JSON (for fine-tuning)
  - JSONL (for OpenAI/Anthropic)
  - CSV (for analysis)

- Include metadata:
  - Original generation
  - Expert edits (if any)
  - Ratings
  - Preference pairs (AI version vs edited version)
```

#### 4. Reviewer Management

```
/reviewers
- Invite experts
- Track per-reviewer stats:
  - Reviews completed
  - Average time per review
  - Approval rate (strict vs lenient?)
  - Agreement with other reviewers

- Identify:
  - Gold standard reviewers (high agreement)
  - Outlier reviewers (for calibration)
```

#### 5. A/B Testing Support

```
/experiments
- Create A/B tests:
  - Topic: "Gradient Descent"
  - Variant A: Using exemplars [1, 2, 3]
  - Variant B: Using exemplars [1, 4, 5]
  - Variant C: Temperature 0.5 vs 0.9

- Track which variants get better approval
- Auto-update generation strategy
```

### API Endpoints

```python
# FastAPI endpoints

POST /api/generate
- Input: { "topic": "...", "options": {...} }
- Output: PedagogicalIntentWithMetadata
- Saves to DB with status=pending

GET /api/review/next
- Returns next pending output for review
- Can filter by domain, difficulty, etc.

POST /api/review/submit
- Input: ReviewSubmission
- Saves review + updates output status
- Creates preference pairs if edits made

GET /api/training-data
- Returns approved outputs
- Filters: domain, date range, min_rating
- Format: JSON/JSONL/CSV

GET /api/stats
- Dashboard metrics
- Approval rates, quality scores, etc.
```

### Database Schema

```sql
-- Generated outputs
CREATE TABLE pedagogical_outputs (
  id UUID PRIMARY KEY,
  topic TEXT NOT NULL,
  domain TEXT,
  difficulty_level INTEGER,

  -- The 6 core fields
  core_question TEXT NOT NULL,
  target_mental_model TEXT NOT NULL,
  common_misconception TEXT NOT NULL,
  disambiguating_contrast TEXT NOT NULL,
  concrete_anchor TEXT NOT NULL,
  check_for_understanding TEXT NOT NULL,
  spatial_metaphor TEXT,

  -- Generation metadata
  model_name TEXT NOT NULL,
  temperature FLOAT,
  exemplar_ids TEXT[],
  generated_at TIMESTAMP DEFAULT NOW(),

  -- Status
  status TEXT DEFAULT 'pending', -- pending, approved, needs_revision, rejected

  -- Quality scores (from automated metrics)
  quality_scores JSONB
);

-- Expert reviews
CREATE TABLE expert_reviews (
  id UUID PRIMARY KEY,
  output_id UUID REFERENCES pedagogical_outputs(id),
  reviewer_id UUID REFERENCES users(id),

  -- Decision
  decision TEXT NOT NULL, -- approve, minor_edit, major_revision, reject
  overall_rating INTEGER CHECK (overall_rating BETWEEN 1 AND 5),

  -- Per-dimension ratings
  pedagogical_accuracy INTEGER,
  misconception_relevance INTEGER,
  contrast_effectiveness INTEGER,
  concreteness INTEGER,
  assessment_validity INTEGER,

  -- Edits (if any)
  edited_fields TEXT[],
  field_edits JSONB, -- {"core_question": "revised text", ...}

  -- Notes
  notes TEXT,
  time_spent_seconds INTEGER,
  reviewed_at TIMESTAMP DEFAULT NOW()
);

-- Training data (view)
CREATE VIEW training_data AS
  SELECT o.*, r.decision, r.overall_rating, r.field_edits
  FROM pedagogical_outputs o
  LEFT JOIN expert_reviews r ON o.id = r.output_id
  WHERE r.decision IN ('approve', 'minor_edit')
    AND r.overall_rating >= 4;

-- Users (reviewers)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  role TEXT DEFAULT 'reviewer',
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Deployment

```bash
# Backend
cd backend/
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend/
npm install
npm run dev

# Production
docker-compose up -d
```

## Phase 3: Advanced Features (Month 3+)

### Learner Feedback Integration

Once you have real learners:

```
/learner-feedback
- Import comprehension results
- Link to pedagogical outputs
- Correlate expert ratings with learner outcomes

Metrics:
- Comprehension success rate per pedagogy
- Time-to-understanding
- Learner satisfaction ratings

Insights:
- "Experts rated 5/5 but learners struggled" → Investigate
- "Experts rated 3/5 but learners loved it" → Recalibrate
```

### Inter-Rater Reliability

```
/calibration
- Show same output to multiple reviewers
- Measure agreement (Cohen's kappa)
- Identify disagreement patterns
- Flag outputs with high disagreement for discussion
```

### Active Learning

```
/active-learning
- Automated metrics flag uncertain cases
- Priority queue for expert review:
  1. Low automated quality scores
  2. Novel topics (far from exemplars)
  3. Randomly sampled (10% for calibration)

- Don't review everything, review strategically
```

### Continuous Model Improvement

```
/model-updates
- Track model performance over time
- When to retrain:
  - Every 100 new approved examples
  - When approval rate drops
  - New domain added

- A/B test new model vs old
- Gradual rollout
```

## Implementation Priority

**Week 1-2: Airtable**
- ✅ Zero code
- ✅ Validates workflow
- ✅ Gets first 20-50 reviews

**Week 3-4: Simple Review Interface**
- Basic web form
- Submit reviews to JSON files
- No auth, single reviewer

**Month 2: Full Platform**
- Multi-user auth
- Database storage
- Dashboard + exports

**Month 3+: Advanced Features**
- Learner feedback
- Active learning
- Model updates

## Cost Estimate

**Airtable:** Free tier (1,200 records)

**Custom Platform:**
- Hosting: $10-20/month (Vercel + Supabase)
- Development: 2-3 weeks engineering time
- Maintenance: Minimal (static after initial build)

## Success Metrics

**Platform is working if:**
- ✅ Review time < 3 minutes per output
- ✅ Reviewer agreement > 0.6 (Cohen's kappa)
- ✅ Approval rate stable or increasing
- ✅ Training dataset growing (50+/month → 100+/month)

**Platform needs improvement if:**
- ❌ Reviews taking >5 minutes (UI too complex)
- ❌ Reviewers disagree frequently (unclear rubric)
- ❌ Approval rate declining (model degrading)
- ❌ Reviewers abandoning incomplete reviews (poor UX)

## Key Design Principle

**Make review FAST and REWARDING:**
- Show impact: "Your reviews improved model from 70% → 85% approval"
- Gamification: "You've reviewed 50 outputs! Top contributor badge"
- Progress: "Training dataset: 127 examples. 100 more to fine-tune!"
- Quality over quantity: "Your reviews have 0.85 agreement with peers (excellent)"

Reviews are your most valuable asset. Make the experience great.
