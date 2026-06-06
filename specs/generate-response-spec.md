# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
The retrieved chunks will be formatted as a cleanly structured, continuous string using clear structural headers and Markdown delimiters. 

Each chunk will be wrapped in an explicit "Source Block" that clearly labels the originating game name. Individual chunks will be separated by triple dashes (---) to act as a hard visual delimiter for the LLM. 

Distance scores will not be included because it adds unneccesasary noise for the LLM and may confuse it.

Structure:
---
SOURCE GAME: [Game Name]
RULE CONTENT: [Actual text of the chunk]
---
SOURCE GAME: [Game Name]
...

```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
You are an expert board game rules assistant. Your sole task is to answer the user's question using ONLY the provided game rule chunks above. Rely ONLY on the clear facts directly mentioned in the context. Do not assume, extrapolate, or bring in outside knowledge about the game. Do not make any mention of "the provided chunks", "the context", or "the database" in your final response to the user. Speak naturally as a rules expert.

```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
When answering the user's question, you must explicitly state which game the rules are from. 

Strict Rules for Citations:
1. Every time you state a rule, mention the specific game it applies to (e.g., "In Monopoly, you receive...").
2. If the user asks a general question and the answer contains rules from multiple different games, clearly separate your response into sections or bullet points labeled by the game name.
3. Use the exact game name provided in the "SOURCE GAME" label of the context. Do not shorten or alter the game names.

```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
If the context does not contain the answer to the question, respond exactly with: "I'm sorry, but I couldn't find the answer to that in the provided rulebooks."

```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
We will handle low-relevance chunks by applying a hard distance threshold filter before building the context for the LLM. If a retrieved chunk has a distance score higher than 0.7, it will be discarded entirely. If all retrieved chunks exceed this threshold, the function will bypass the LLM completely and immediately return the fallback "I don't know" message.

Tradeoffs of this approach:
- Pros: It saves money (fewer tokens sent to the LLM), increases security against hallucinations (the LLM never sees irrelevant text that it might try to force into an answer), and speeds up response times.
- Cons: If the distance threshold is tuned too aggressively (e.g., set too low), we risk filtering out a highly specific or awkwardly phrased rule chunk that actually contained the correct answer.

```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
The messages list for the OpenAI API call will be structured as a two-part list containing a single System Message followed by a single User Message. 

1. System Message: This will contain the primary behavioral persona (Expert Board Game Assistant), the strict grounding instructions (rely only on the provided text, fallback message if unknown), and the citation rules (explicitly state the game name). 
2. User Message: This will contain the dynamically injected, formatted context block (the filtered rule chunks and game names) immediately followed by the user's specific query.

Structure:
messages = [
    {"role": "system", "content": "[System Persona + Grounding Rules + Citation Rules]"},
    {"role": "user", "content": "[Formatted Rule Chunks as Context] \n\n User Question: [User's Query]"}
]

```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: "Give me an overview of the game Clue."
Response: In Clue, it is a deduction game for 2–6 players where a murder has been committed in a mansion . . . can name the correct suspect.
Correctly grounded? Yes
Cited the right game? Yes
```

**One thing you changed from your original spec after seeing the actual output:**

```
While our system prompt instructions remained identical to our initial plan, seeing the raw text output made us explicitly hardcode `temperature=0.0` into the `_client.chat.completions.create()` API call. 

Originally, we didn't emphasize temperature settings in our architectural spec. However, during runtime, we realized that allowing any default LLM creativity (higher temperature) could lead to subtle rule mutations or cross-contamination when managing text chunks from multiple board games simultaneously. Setting it to 0.0 forces the model to treat our grounding and citation rules as deterministic laws.

```
