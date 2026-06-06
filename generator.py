from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.

    TODO — Milestone 3:

    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"     : the chunk text
      - "game"     : the game name
      - "distance" : similarity score (you can use this to filter weak matches)

    Before writing code, talk through these with your group:
      - How will you format the chunks into a context block for the prompt?
      - What instructions will stop the model from answering beyond what the
        rules say? (Grounding is the whole point — a confident wrong answer
        is worse than an honest "I don't know.")
      - How will you surface which game each answer comes from?

    Your response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which game the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Your implementation here.

    """
    Milestone 3 Completed:
      1. Filters out low-relevance chunks (distance > 0.7).
      2. Formats remaining chunks with clear game labels and delimiters.
      3. Passes strict grounding and citation rules via the system prompt.
      4. Returns a plain string response.
    """
    # fallback response for empty retrieval
    fallback_message = "I'm sorry, but I couldn't find the answer to that in the provided rulebooks."

    if not retrieved_chunks:
        return fallback_message

    # 1. Handling low-relevance chunks (Filter out anything > 0.7)
    filtered_chunks = [chunk for chunk in retrieved_chunks if chunk["distance"] <= 0.7]
    
    # If no chunks survive the filter, bypass the LLM and return fallback immediately
    if not filtered_chunks:
        return fallback_message

    # 2. Context formatting using the agreed structural layout
    context_blocks = []
    for chunk in filtered_chunks:
        block = (
            f"---\n"
            f"SOURCE GAME: {chunk['game']}\n"
            f"RULE CONTENT: {chunk['text']}\n"
            f"---"
        )
        context_blocks.append(block)
    
    formatted_context = "\n".join(context_blocks)

    # 3. Message structure: System prompt (Grounding + Citation) & User prompt
    system_prompt = (
        "You are an expert board game rules assistant. Your sole task is to answer the user's question "
        "using ONLY the provided game rule chunks above.\n\n"
        "Strict Rules for Grounding:\n"
        "1. Rely ONLY on the clear facts directly mentioned in the context. Do not assume, extrapolate, "
        "or bring in outside knowledge about the game.\n"
        "2. If the context does not contain the answer to the question, respond exactly with: "
        f"\"{fallback_message}\"\n"
        "3. Do not make any mention of 'the provided chunks', 'the context', or 'the database' in your final "
        "response to the user. Speak naturally as a rules expert based on what you know.\n\n"
        "Strict Rules for Citations:\n"
        "1. Every time you state a rule, mention the specific game it applies to (e.g., 'In Monopoly, you receive...').\n"
        "2. If the user asks a general question and the answer contains rules from multiple different games, "
        "clearly separate your response into sections or bullet points labeled by the game name.\n"
        "3. Use the exact game name provided in the 'SOURCE GAME' label of the context. Do not shorten or alter it."
    )

    user_prompt = f"{formatted_context}\n\nUser Question: {query}"

    # 4. Execute the API call
    chat_completion = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0  # Kept at 0.0 to ensure deterministic, highly-grounded responses
    )

    # Return the final text string response
    return chat_completion.choices[0].message.content


# --- TEST ----
# from retriever import retrieve

# if __name__ == "__main__":
#     # 1. Ask a live question
#     test_query = "Give me an overview of the game Clue."
    
#     print("--- STARTING LIVE RAG PIPELINE ---")
#     print(f"1. User Query: '{test_query}'\n")
    
#     # 2. Call your actual retrieve.py function to pull from ChromaDB
#     print("2. Fetching chunks from ChromaDB...")
#     live_chunks = retrieve(test_query, n_results=3)
    
#     # Check if the database actually returned anything before moving on
#     if not live_chunks:
#         print("❌ Search returned 0 results. Is your database empty?")
#     else:
#         print(f"   Success! Found {len(live_chunks)} chunks.\n")
        
#         # 3. Feed those live database chunks straight into your LLM generator
#         print("3. Sending grounded context to Groq LLM...")
#         response = generate_response(test_query, live_chunks)
        
#         print("\n--- FINAL LLM RESPONSE ---")
#         print(response)
#         print("---------------------------")