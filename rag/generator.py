"""
RAG Generator — Uses GPT-4o-mini to produce policy-grounded explanations.
"""
from openai import OpenAI
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import OPENAI_API_KEY, LLM_MODEL

log = get_logger("rag.generator")

_client = None


def _get_client() -> OpenAI:
    """
    Initializes and caches the OpenAI client instance.
    Uses the API key configured in the settings.
    """
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a healthcare claims policy expert. Given a claim's denial reasons 
and relevant policy excerpts, provide a clear, concise explanation of:
1. Why the claim is at risk of denial
2. Which specific policy rules are relevant
3. What the billing team should do to fix the claim

Keep your response under 200 words. Be specific and actionable."""


def generate_explanation(claim_context: str, policy_chunks: list[dict], reasons: list[str]) -> str:
    """
    Constructs a prompt using the claim details, ML denial reasons, and retrieved policy chunks,
    and calls the LLM to generate a plain-English explanation.
    
    Args:
        claim_context (str): Summary string of the claim details.
        policy_chunks (list[dict]): Retrieved policy chunks from the vector store.
        reasons (list[str]): Top features that contributed to the model's prediction.
        
    Returns:
        str: A generated explanation summarizing the risk and required fixes.
    """
    # Extract and format the text from the top 3 policy chunks
    policy_text = "\n\n".join([f"[{c.get('section', 'Policy')}]: {c['text'][:500]}" for c in policy_chunks[:3]])

    # Build the prompt for the LLM
    user_prompt = f"""Claim Details:
{claim_context}

Denial Risk Reasons:
{chr(10).join(f'- {r}' for r in reasons)}

Relevant Policy Excerpts:
{policy_text}

Provide a brief explanation and recommendation."""

    try:
        client = _get_client()
        # Call the OpenAI API using the specified model (e.g. GPT-4o-mini)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3, # Low temperature for more deterministic, policy-adherent output
            max_tokens=400,
        )
        explanation = response.choices[0].message.content
        log.info("LLM explanation generated (%d chars)", len(explanation))
        return explanation
    except Exception as exc:
        log.error("LLM generation failed: %s", exc)
        return f"Unable to generate explanation: {str(exc)}"
