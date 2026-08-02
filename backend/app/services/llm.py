import os

import requests

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

FALLBACK_MESSAGE = (
    "Kunne ikke generere en AI-anbefaling lige nu (LLM'en svarede ikke). "
    "Prøv igen om lidt, eller tjek at Ollama-servicen kører."
)


def _build_prompt(summary_text: str) -> str:
    return (
        "Du er en hjælpsom fitness- og ernæringscoach. "
        "Her er brugerens loggede data for de seneste 7 dage:\n\n"
        f"{summary_text}\n\n"
        "Giv en kort, konkret anbefaling (maks 5 sætninger) om kost og "
        "træning baseret på disse data. Skriv på dansk, i en venlig og "
        "motiverende tone."
    )


def _call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=110,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", FALLBACK_MESSAGE).strip()
    except (requests.RequestException, ValueError):
        return FALLBACK_MESSAGE


def _call_mistral(prompt: str) -> str:
    if not MISTRAL_API_KEY:
        return FALLBACK_MESSAGE

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    payload = {
        "model": MISTRAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(MISTRAL_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return FALLBACK_MESSAGE


def generate_recommendation(summary_text: str) -> str:
 
    prompt = _build_prompt(summary_text)

    if LLM_PROVIDER == "mistral":
        return _call_mistral(prompt)

    return _call_ollama(prompt)
