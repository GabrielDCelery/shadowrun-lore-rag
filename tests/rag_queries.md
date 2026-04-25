# RAG Evaluation Queries

Each entry has:
- **Q**: the query as a user would ask it
- **Source**: book and section where the answer lives
- **Category**: `factual` (direct lookup) | `inference` (requires combining facts) | `cross-book` (spans multiple sources)
- **Expected**: what a good answer must contain (not a verbatim answer — key facts that must be present)

---

## Tir Tairngire (`7210---tir-tairngire`)

### Q1 — factual
**Q:** What is the population of Tir Tairngire and what is its racial composition?

**Source:** Tir Tairngire — First Impressions / Facts at a Glance

**Expected:**
- Total population approximately 5,610,000
- 85% elf, 7% dwarf, 5% ork, 1% human, 2% other

---

### Q2 — factual
**Q:** How does the Rite of Progression work in Tir Tairngire?

**Source:** Tir Tairngire — Tir Society / Rite of Progression

**Expected:**
- Held every 7 years (last 2050, next 2057)
- Determines or confirms social rank
- Two components: bureaucratic testing (multi-day computer tests) and physical testing (The Games — seven events, candidate picks four)
- Results announced two weeks after the Rite; binding, no appeal until next cycle
- Lobbying of the Proctor's office is permitted in the 12 months prior

---

### Q3 — factual
**Q:** What are the penalties for possessing an automatic weapon in Tir Tairngire?

**Source:** Tir Tairngire — Laws

**Expected:**
- Possession: 22,000¥ fine and 1 year imprisonment
- Transport: 44,000¥ and 1 year
- Threatening with one: 3 years
- Using one: 4 years
- Autofire weapons are banned entirely in Tir Tairngire

---

### Q4 — inference
**Q:** Why is Portland's economy struggling in 2054 and what caused the decline?

**Source:** Tir Tairngire — Economy / Portland

**Expected:**
- In 2052 the Council shifted primary trade from Portland to Seattle
- Billions of nuyen in import/export previously passed through Portland in the 2040s boom
- Many businesses went bankrupt, fortunes were lost
- Portland now serves only as a cargo way station with limited actual trading
- The Council decision (not any external event) is the cause

---

### Q5 — inference
**Q:** What evidence exists that Ehran the Scribe and Walter Bright Water are the same person?

**Source:** Tir Tairngire — Political Profiles

**Expected:**
- Both are tall slender elves with the same build and facial bone structure
- Computer-altered image of Bright Water without beard in Ehran's haircut shows profound facial similarities
- Bright Water announced terminal cancer in 2028/2029 and died shortly after — Ehran emerged post-2030
- Bright Water had detailed knowledge of Cascade Crow traditions inconsistent with his claimed background
- Key differences (hair colour, beard) are cosmetic and achievable via magic

---
