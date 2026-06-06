# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
To find relevant chunks, we will call `_collection.query()` inside the retrieval function, passing three explicit arguments to customize the semantic search behavior:

1. `query_texts=[query]`: We pass the user's raw string question wrapped inside a single-element list. This tells ChromaDB to automatically convert the text into a vector embedding using our pre-configured SentenceTransformer translator.
2. `n_results=n_results`: We pass the desired number of matches to return (defaulting to the N_RESULTS constant). This controls how many of the top mathematically relevant rule pieces are pulled back.
3. `include=["documents", "metadatas", "distances"]`: We pass this list to explicitly request the raw rule text, the game name tracking metadata, and the cosine similarity score. Omitting this would prevent us from knowing which game a rule belongs to or executing our distance threshold filter.

```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
{
    "text": " If a Wild Draw Four is played against you, you may challenge the player who played it. The player must show their hand privately to the challenger. If the challenge is successful (the player had a matching color card they could have played), they must draw 4 cards instead of you. If the challenge fails, you must draw 6 cards (the original 4 plus 2 more) and lose your turn.",
    "game": "uno",
    "distance": 0.3142
}
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
Because we are only passing a single query, we need to access index [0]. The nesting exists so that ChromaDB can accept a batch of multiple queries at once and return a distinct list of results for each one.
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
The `retrieve()` function will return all n_results regardless of their distance scores. We are intentionally deferring the relevance filtering to the downstream `generate_response()` function (Milestone 3). 

Tradeoffs of Deferring the Filter to the Generator:
- Pros: It preserves a clean separation of concerns. `retrieve()` behaves purely as a data-fetcher, providing full visibility into what the database found. This allows the generator function to inspect the data, look at the distribution of scores, and apply a uniform 0.7 distance cutoff right before building the prompt.
- Cons: `retrieve()` passes along potentially "noisy" or completely irrelevant chunks to the next step, meaning the downstream function must always implement rigid defensive guards to clean up the data array before processing it.

```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
Our implementation is designed with defensive guardrails to handle these three distinct scenarios gracefully:

(a) When the collection is empty:
The `retrieve()` function instantly catches this via an early guardrail (`if _collection.count() == 0: return []`). Because an empty list is returned to `generate_response()`, the function triggers its automated fallback logic, bypassing the Groq API call entirely, and immediately returns the standard message: "I'm sorry, but I couldn't find the answer to that in the provided rulebooks."

(b) When the query matches no chunks well:
ChromaDB will still fetch the top n_results, but they will have high distance scores (e.g., > 0.7). Inside `generate_response()`, our list comprehension filter (`chunk["distance"] <= 0.7`) will scrub these weak matches out, leaving `filtered_chunks` empty. The function detects this empty list and immediately returns our fallback "I don't know" message without making an API call, preventing the LLM from hallucinating an answer out of irrelevant text.

(c) When the query matches chunks from multiple games:
Our context formatter will isolate each chunk into independent structural blocks, clearly identifying the source game for each paragraph using explicit headers. Because our System Prompt includes a strict "Rules for Citations" directive, the LLM will actively recognize the different game names, separate its response into distinct bullet points or sections, and properly credit each rule to its respective game (e.g., "In Monopoly, you... while in Catan, you..."). This completely prevents cross-contamination of rules.

```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: "How do you get out of jail in Monopoly?"
Top result game: Monopoly
Distance score: 0.367
Does it make sense? No. The returned chunk is specifically about going to Jail in Monolopy but not how you get out of jail once you are in.

```

**One thing about the query results that surprised you:**

```
The results may be correctly pointing to the right game and subject, but more specificity is needed when asking about specific turns of events (i.e. getting out of jail in Monopoly vs getting sent to jail).

```
