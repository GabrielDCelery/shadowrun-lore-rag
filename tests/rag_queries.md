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

## Tir na nÓg (`7211---tir-na-nog`)

### Q6 — factual

**Q:** What are the airfares from Tir na nÓg to other major cities, and how do they compare in both nuyen and Irish punts?

**Source:** Tir na nÓg — Travel / Transport

**Expected:**

- Irish punt exchange rate: £2.20 = 1¥
- London: 160¥ / £352
- Paris: 200¥ / £440
- Seattle: 1,850¥ / £4,070
- Tokyo: 2,600¥ / £5,720
- Transorbital: 4,600¥ / £10,120

---

### Q7 — factual

**Q:** What are the ferry routes available from Tir na nÓg and what do they cost?

**Source:** Tir na nÓg — Travel / Transport

**Expected:**

- Larne to Stranraer: 70¥
- Dublin to Liverpool: 100¥
- Ferries are significantly cheaper than air travel for reaching Britain

---

### Q8 — inference

**Q:** Why do no dragons live in Tir na nÓg, and what does this suggest about relations between elves and dragons?

**Source:** Tir na nÓg — Dragons / Magical Ecology

**Expected:**

- No great dragons or lesser dracoforms are found within Tir na nÓg
- Elves and dragons do not coexist in the same heartland — one excludes the other
- This is a pattern, not coincidence: wherever elves establish a homeland, dragons are absent
- Tir Tairngire likewise has no resident great dragons despite being a powerful magical nation
- The relationship is one of mutual exclusion at the level of magical territory

---

## Denver: The City of Shadows (`7212---denver---the-city-of-shadows`)

### Q9 — factual

**Q:** What is Denver's total population in 2055 and how is it broken down by race and SIN status?

**Source:** Denver — Facts at a Glance

**Expected:**

- Total population: 3,620,000 (May 2055)
- 62% human
- SINless population: 543,000
- Per capita income: 21,750¥
- 29% below the poverty line

---

### Q10 — factual

**Q:** What are the fares and travel times on Denver's maglev rail system?

**Source:** Denver — Transport / Maglev

**Expected:**

- Express route (Boulder to Colorado Springs): under 1 hour
- Commuter line: 43 stops, approximately 4 hours end to end
- Fares range from 2¥ to 85¥ depending on distance
- Altitude of Denver is 1,609 metres / 5,280 feet
- Alcohol is 1.5 times more potent at Denver's altitude

---

### Q11 — inference

**Q:** What makes Denver uniquely valuable as a location for intelligence gathering and espionage in 2055?

**Source:** Denver — Overview / Political Structure

**Expected:**

- Denver is divided into six sectors controlled by different nations: Aztlan, CAS, Pueblo, Sioux, UCAS, and Ute
- Each sector has its own RTG (Regional Telecommunications Grid) and jurisdiction
- The divided jurisdiction means no single authority controls the whole city
- Intelligence agencies from multiple nations and megacorps operate in the city simultaneously
- Shadowrunners can cross between sectors and exploit jurisdictional gaps
- The city hosts 7 international airports, facilitating movement

---

## Aztlán (`7213---aztlán`)

### Q12 — factual

**Q:** What happened to Mexico City during the VITAS outbreak of 2010?

**Source:** Aztlán — History

**Expected:**

- Mexico City had a population of over 23 million at the time
- VITAS killed more than 12% of the population
- The death toll in Mexico City alone was in the millions
- The catastrophe destabilised the existing political order, enabling ORO Corp to gain power

---

### Q13 — factual

**Q:** What corporations participated in Operation RECIPROCITY in 2048, and what were the results?

**Source:** Aztlán — Corporate Relations / History

**Expected:**

- Operation RECIPROCITY was a strike on Ensenada (Aztlan territory) in 2048
- Attacking corps: Ares, Fuchi, Mitsuhama, Saeder-Krupp
- Logistics support from: Yamatetsu, Renraku, Shiawase
- Aztlan forces suffered approximately 15% losses
- The operation demonstrated that even the Big Ten could combine against Aztlan when provoked

---

### Q14 — inference

**Q:** What does the origin of ORO Corporation reveal about the relationship between organised crime and corporate power in Aztlan?

**Source:** Aztlán — Corporate History / ORO Corp

**Expected:**

- ORO Corp was founded in 2007
- The name ORO comes from the initials of the three founding drug cartel families: Ortega, Ramos, and Oriz
- ORO Corp built Aztlan's direct-democracy electoral system, embedding political control from the start
- Francisco Pavón was elected on May 5, 2015 under this system
- Aztechnology, the world's largest consumer goods corp, grew directly from these narco-cartel roots

---

## Bug City (`7117---bug-city`)

### Q15 — factual

**Q:** What was the precise sequence of events during the first 24 hours of the Chicago insect spirit outbreak in August 2055?

**Source:** Bug City — Timeline / The Outbreak

**Expected:**

- Swarm erupted at approximately 4 PM on August 22, 2055, west of the Shattergraves
- Eagle Security fielded the first calls
- Chicago LTG (Local Telecommunications Grid) was shut down at 21:01:56 on August 23
- UCAS military VTOLs were stationed at Meigs Field
- The government publicly claimed the disturbance was a new strain of VITAS

---

### Q16 — factual

**Q:** What weapon was used to attempt to contain the Chicago insect spirit outbreak, and when was it deployed?

**Source:** Bug City — Military Response

**Expected:**

- A subtactical nuclear weapon was detonated just before dawn on September 1st
- Ares Macrotechnology is connected to the nuclear strike (they maintain low-yield devices for surgical strikes)
- Hundreds of thousands — possibly over one million people — were trapped inside the Containment Zone

---

### Q17 — inference

**Q:** Why did the UCAS government's public explanation for the Chicago outbreak fail to hold up, and what does this reveal about official information control in the Sixth World?

**Source:** Bug City — Government Response / Timeline

**Expected:**

- The government claimed a new VITAS strain caused the crisis
- The Chicago LTG was shut down to prevent information from leaking out — a power grid failure would not explain selective communications blackout
- Military VTOLs and a nuclear detonation are inconsistent with a disease outbreak response
- The scale of the Containment Zone (hundreds of thousands trapped) contradicts a quarantine story
- The speed and nature of the response (nuclear weapon within 10 days) indicates the government knew the true nature of the threat from the start

---

## Germany Sourcebook (`7204---germany-sourcebook`)

### Q18 — factual

**Q:** What is the racial composition and life expectancy in Germany, and how does income affect longevity?

**Source:** Germany — Demographics / Facts at a Glance

**Expected:**

- Total population: 98.3 million (299 per square kilometre)
- Racial breakdown: 68% human, 17% dwarf, 8% troll, 4% ork, 3% elf
- Average life expectancy ranges from 59.6 years (lowest income) to 107.1 years (highest income)
- Per capita income: EC 31,000
- 25% of the population are pagan or polytheist

---

### Q19 — factual

**Q:** What are the airfares from Germany to other cities, and what are the costs of imported goods in the AGS?

**Source:** Germany — Transport / Economics

**Expected:**

- Airfares (one-way in ECU): Paris 100, London 160, Seattle 1,500, Tokyo 1,900, Sydney 2,200
- Foreign product price surcharges: weapons 200%, American vehicles 200%, Japanese vehicles 90%, American cyberware 200%
- Three currencies in use: ECU, nuyen, and Deutschmark at a 1:1:2 ratio

---

### Q20 — inference

**Q:** What was the long-term human cost of the Cattenom nuclear accident, and what does the timeline reveal about radiation's slow toll?

**Source:** Germany — History / Cattenom

**Expected:**

- Cattenom Block 2 exploded on March 4, 2009 at 10:08
- Immediate deaths: 37,241
- Total deaths by 2045: 135,728
- The gap between immediate and total deaths (nearly 100,000 more over 36 years) shows the long-term cancer and radiation illness burden
- The accident predates the Awakening, meaning no magical healing was available to early victims

---

## Neo-Anarchist's Guide to North America (`7206---shadowrun---neo-anarchists-guide-to-north-america`)

### Q21 — factual

**Q:** How did the Confederation of American States form, and which states joined?

**Source:** Neo-Anarchist's Guide — CAS Section

**Expected:**

- The CAS formed when 10 southern states seceded from the newly created UCAS
- Formation formalised through the Treaty of Richmond
- The Act of Union in 2030 had merged the United States and Canada into the UCAS
- Aztlan seized Austin and San Antonio from Texas in 2035
- The CAS established its own intelligence agency, the Department of Strategic Intelligence (DSI)

---

### Q22 — factual

**Q:** What were the key events that led to California declaring independence and forming the California Free State?

**Source:** Neo-Anarchist's Guide — California Free State Section

**Expected:**

- Anti-Indian riots occurred in California in 2009
- Nelson Treacle was governor during this period
- California declared independence in 2037
- MacAlister's famous "Eat My Shorts" speech was a landmark moment in the independence movement
- The California Free State (CFS) sits between Tir Tairngire to the north and Aztlan to the south

---

### Q23 — inference

**Q:** What do the fates of Texas and California after the fragmentation of the United States reveal about the relationship between geographic position and political survival?

**Source:** Neo-Anarchist's Guide — CAS / CFS Sections

**Expected:**

- Texas lost major cities (Austin and San Antonio) to Aztlan expansion in 2035
- California managed to maintain independence in 2037 despite pressure from multiple sides
- California's coastline and economic base gave it leverage that landlocked or border regions lacked
- Texas, bordering Aztlan directly, proved more vulnerable to territorial loss
- Nations that bordered multiple powers (California bordered Tir Tairngire, Pueblo, Aztlan) had to balance relationships rather than resist one dominant neighbour

---

## Year of the Comet (`10650---year-of-the-comet`)

### Q24 — factual

**Q:** What are the orbital characteristics of Halley's Comet as recorded in 2061, and when was it visible to the naked eye?

**Source:** Year of the Comet — Astronomical Data

**Expected:**

- Perihelion: 0.6 AU from the Sun
- Orbital inclination: 162.2 degrees
- Orbital period: approximately 76 years
- Visible to the naked eye: September through late November 2061
- The UN officially declared 2061 the "Year of the Comet"

---

### Q25 — factual

**Q:** What were the two corporate probes sent to Halley's Comet in 2061, and what happened to them?

**Source:** Year of the Comet — Corporate Race / Space Probes

**Expected:**

- Ares launched the _Gigas_: 8 tonnes, cost 2 billion nuyen, fusion drive, launched to public fanfare
- Saeder-Krupp launched the _Duccio_: designed to land on the comet surface with no return capability
- Ares destroyed the _Duccio_ using an anti-satellite laser, claiming it was an accident
- The Corporate Court ruled in favour of Ares in the subsequent settlement
- Velox I and II probes were also sent to pass through the comet tail

---

### Q26 — inference

**Q:** What does Ares Macrotechnology's destruction of the Saeder-Krupp probe reveal about corporate competition and the limits of Corporate Court authority?

**Source:** Year of the Comet — Corporate Relations / Space Race

**Expected:**

- Ares destroyed a competitor's probe using a military-grade anti-satellite laser — an act of sabotage in space
- Ares publicly claimed it was an accident, providing deniability
- The Corporate Court ruled in Ares's favour despite the suspicious circumstances
- Saeder-Krupp (run by the great dragon Lofwyr) was unable to obtain meaningful redress through official channels
- This demonstrates that corporations with government connections (Ares owns former NASA assets) can act with impunity even against fellow megacorps

---

## State of the Art: 2064 (`25004---state-of-the-art-2064`)

### Q27 — factual

**Q:** Which organisations and nations own spy satellites with optical, infrared, and radar scanning capabilities as of 2064?

**Source:** State of the Art: 2064 — Games of State / Satellite Imagery Availability Table

**Expected:**

- UCAS (partnered with AresSpace): optical 5, infrared 9, radar 10 — the highest radar capability
- Russia (UGB): optical 8, infrared 6, radar 8 — highest optical capability
- Novatech Orbital: optical 6, infrared 9, radar 8
- CAS (DSI/ERLA): optical 6, infrared 8, radar 6
- Only a small number of agencies own their own satellites; others borrow through alliances

---

### Q28 — factual

**Q:** What is the Seraphim, and how is it internally organised?

**Source:** State of the Art: 2064 — The Playing Pieces / The Seraphim

**Expected:**

- The Seraphim is the intelligence arm of Cross Applied Technologies
- Headquarters: L'Assomption, Quebec; Chief Executive Director: Antoine Carsieur
- Operatives are classified H1 (external/shadowrunners) through H10 (unknown function, possibly answers only to Lucien Cross)
- Assignments are classified C1 (passive observation, routine) through C9 (covert action, destructive, urgent)
- The H10 category is unknown even within the intelligence community

---

### Q29 — inference

**Q:** What does the fate of the Dunkelzahn Watchers network after the dragon's death reveal about intelligence organisations' dependence on their founders?

**Source:** State of the Art: 2064 — Games of State / The Watchers

**Expected:**

- Dunkelzahn ran a cell-based intelligence network called the Watchers with himself at the top
- After Dunkelzahn's assassination in 2057, the network gradually fragmented without its master
- The Draco Foundation absorbed approximately one-third of the Watchers
- Ghostwalker absorbed approximately one-third after emerging through the Dunkelzahn Rift
- The remaining third went independent or transferred allegiance to other dragons
- The lesson: even the most sophisticated intelligence network collapses without centralised leadership and purpose

---

## Sprawl Survival Guide (`10667---sprawl-survival-guide`)

### Q30 — factual

**Q:** What legal powers do law enforcement officers have over civilians in the UCAS as of 2063?

**Source:** Sprawl Survival Guide — Society / Law and Jurisdiction

**Expected:**

- Officers may detain any suspect for up to 72 hours without charging them
- Police may stop any person or vehicle at any time to check ID, registration, and insurance
- Personal searches and astral scans are allowed without warrants
- Private property may be searched without a warrant if the officer has probable cause
- Investigators do not need warrants to request Matrix logs, credit histories, or phone records
- Wire-taps and mind probes are the only forms of surveillance requiring authorisation

---

### Q31 — factual

**Q:** What are the approximate costs of different modes of long-distance travel in 2063?

**Source:** Sprawl Survival Guide — Travel / It's a Small World

**Expected:**

- HSCT flight (Seattle to Vladivostok, round trip): approximately 1,800¥
- Suborbital flight (round trip, most international airports): approximately 2,500¥
- Semiballistic flight (round trip): approximately 4,000¥
- Train (London Waterloo to Paris Nord, 494 km): 280¥
- Train (Seattle to New York Penn Station): 450¥
- Bus (Seattle to Washington DC, round trip): approximately 300¥
- Car rental: approximately 60¥ per day

---

### Q32 — inference

**Q:** What does the metahuman population's position in UCAS society in 2063 suggest about the limits of legal equality?

**Source:** Sprawl Survival Guide — Society / Lines in the Sand

**Expected:**

- Metahumans make up approximately 15% of the UCAS population
- Less than 1% of Fortune 500 CEOs are orks or trolls
- Average metahuman wages are 17% below the national average
- Orks and trolls make up 42% of the prison population despite being a minority
- Approximately twice as many metahumans as humans are SINless
- A specific Act of Congress is still required to bestow full citizenship on sentient non-Homo sapiens beings
- Legal equality on paper does not translate into economic or social equality in practice

---

## Shadowrun Fourth Edition Core Rules (`shadowrun4thedition-corerules`)

### Q33 — factual

**Q:** What are the ten largest megacorporations in the Shadowrun world as of 2070, and where is each headquartered?

**Source:** Shadowrun 4th Edition — Life on the Edge / The Big Ten

**Expected:**

- Ares Macrotechnology: Detroit, Michigan, UCAS
- Aztechnology: Tenochtitlán, Aztlan
- Evo Corporation (formerly Yamatetsu): Vladivostok, Russia
- Horizon: Los Angeles, Pueblo Corporate Council
- Mitsuhama Computer Technologies: Kyoto, Japan
- NeoNET: Boston, Massachusetts, UCAS
- Renraku Computer Systems: Chiba, Japan
- Saeder-Krupp Heavy Industries: Essen, Germany
- Shiawase Corporation: Osaka, Japan
- Wuxing, Incorporated: Hong Kong Free Enterprise Enclave

---

### Q34 — factual

**Q:** What street slang terms were commonly used in 2070, and what do they mean?

**Source:** Shadowrun 4th Edition — Common Street Slang in 2070

**Expected:**

- "Dandelion eater" or "keeb": derogatory term for elf
- "Halfer", "stuntie", or "squat": derogatory term for dwarf
- "Mr. Johnson": name adopted by a person who hires shadowrunners
- "Paydata": a datafile worth money on the black market
- "Wizworm": dragon
- "Vatjob": a person with extensive cyberware replacement
- "Smoothie": derogatory term for non-ork or non-troll

---

### Q35 — inference

**Q:** What does the Corporate Court's structure and the principle of extraterritoriality reveal about who actually governs the Sixth World?

**Source:** Shadowrun 4th Edition — Life on the Edge / Extraterritoriality / Guarding the Henhouse

**Expected:**

- Extraterritoriality means megacorps enforce their own laws on their own territory — governments have no authority there
- The Corporate Court consists of 13 justices drawn from the Big Ten megacorps
- The Court has no enforcement mechanism — it relies on the megas' shared interest in avoiding chaos
- Only the Corporate Court can grant extraterritorial status, making membership self-reinforcing
- The Court is based at the Zurich Orbital habitat, the most secure facility on or off Earth
- Nation-states passed laws, but the Shiawase court decision created extraterritoriality — a corporation changed the fundamental rules of governance

---

## Bullets & Bandages (`shadowrun-5e-bullets-bandages`)

### Q36 — factual

**Q:** What is DocWagon's corporate structure and when was it founded?

**Source:** Bullets & Bandages — DocWagon at a Glance

**Expected:**

- Founded: 2037
- Corporate status: AA megacorporation
- World headquarters: Atlanta, CAS
- President: Thomas Abston, M.D.
- CEO: Anderson Gentry
- Major divisions: North America, South America, Europe, PanAsia
- Tagline: "When your life is on the line, DocWagon is on the way"

---

### Q37 — factual

**Q:** What are the contents and costs of medkits by rating, and how does size change with rating?

**Source:** Bullets & Bandages — Medkit Component Table

**Expected:**

- Rating 1 (100¥): bandages, tape, scissors, basic drug database — fits in a large pocket (–2 conceal)
- Rating 2 (400¥): adds splints, syringes, antibiotics — small pouch/fanny pack (–1 conceal)
- Rating 3 (900¥): adds airway supplies, IV tubing, oxygen mask — large pouch (+0 conceal)
- Rating 4 (1,600¥): adds basic surgical tools, slap patches, rigger adaptation — small backpack (+1 conceal)
- Rating 5 (2,500¥): adds injectable nanite treatments, StatScan imager — large backpack (+2 conceal)
- Rating 6 (3,600¥): adds full surgical tools, anesthetic gases, DocWagon pay-per-use service — oversized duffel bag or larger (+3 conceal)

---

### Q38 — inference

**Q:** Why might a shadowrunner choose to carry a lower-rated medkit even though higher-rated kits are more medically capable?

**Source:** Bullets & Bandages — Medkit Component Table / Upgrading Medkits

**Expected:**

- Higher-rated medkits are larger and harder to conceal (a Rating 6 kit requires an oversized duffel bag with a +3 concealability penalty)
- A Rating 1 kit fits in a large pocket; a Rating 6 kit cannot be hidden
- In combat or infiltration scenarios, carrying a large visible medkit creates a tactical liability
- Medkits can be upgraded to increase their Rating while retaining their original size, but this requires a successful Cybertechnology + Logic extended test
- The cost of upgrading is equal to the full purchase price of the target-Rating kit
- The trade-off between medical capability and operational concealability mirrors the broader shadowrunner dilemma of effectiveness vs. mobility

---

## Cross-Book Queries (`cross-book`)

### XQ1 — cross-book (Tir Tairngire + Tir na nÓg)

**Q:** Both Tir Tairngire and Tir na nÓg are elven nations founded in the early 21st century. What do their population figures and founding circumstances reveal about the different scales of elven political ambition?

**Sources:**

- Tir Tairngire — Facts at a Glance
- Tir na nÓg — Demographics / History

**Expected:**

- Tir Tairngire population: approximately 5,610,000 (85% elf)
- Tir na nÓg population: approximately 4,000,000
- Tir Tairngire was carved out of the Pacific Northwest of North America — a deliberate separatist act in a heavily populated region
- Tir na nÓg reclaimed the island of Ireland, which had an existing cultural and mythological identity supporting the elven claim
- Neither nation tolerates dragons within its heartland — a shared trait suggesting a common magical dynamic
- Tir Tairngire holds the Rite of Progression every 7 years to confirm social rank; Tir na nÓg rescheduled its own equivalent ceremonies during the Year of the Comet

---

### XQ2 — cross-book (Bug City + Year of the Comet)

**Q:** The Chicago insect spirit outbreak (2055) and the return of Halley's Comet (2061) are both presented as world-changing events. What do they share in terms of how information was managed and suppressed?

**Sources:**

- Bug City — Government Response / Timeline
- Year of the Comet — SURGE / Corporate Response

**Expected:**

- In both cases governments and corporations initially provided false or misleading public explanations (VITAS for Chicago; "accident" for the Ares destruction of the Duccio probe)
- The Chicago LTG was physically shut down to prevent information from escaping the Containment Zone
- Ares used the Corporate Court process — a controlled, non-public mechanism — to settle the probe destruction rather than face public scrutiny
- In both cases, the scale of events eventually made suppression impossible: the Containment Zone was too large to hide, and the comet's effects (SURGE transformations) were visible worldwide
- Both events demonstrated that official institutions (UCAS government, Corporate Court) serve the interests of the powerful rather than the public

---

### XQ3 — cross-book (Germany Sourcebook + State of the Art: 2064)

**Q:** Germany and the Allied German States appear in both the Germany Sourcebook and State of the Art: 2064. What do the two books together reveal about Germany's strategic position in European intelligence and military affairs?

**Sources:**

- Germany Sourcebook — Economy / Demographics / Military
- State of the Art: 2064 — Games of State / Argus / Brussels

**Expected:**

- Germany has the largest population in Europe at 98.3 million, making it a major power base
- Argus, the intelligence arm of mercenary group MET 2000, is headquartered in Baumholder, Badisch-Pfalz (AGS)
- Argus performs the majority of non-military intelligence for the Allied German States — Germany outsources its spy work to a mercenary organisation
- The Frankfurt Bank Association (FBA) had ties to the great dragon Nachtmeister before his death at Lofwyr's claws in 2062
- Saeder-Krupp (headquartered in Essen, Germany) is the largest corporation in the world, meaning Germany hosts both the world's biggest corp and the EU's primary intelligence-for-hire agency
- The Cattenom nuclear accident in 2009 (37,241 immediate deaths) shaped German public attitudes toward nuclear power even as France continues underground testing nearby
