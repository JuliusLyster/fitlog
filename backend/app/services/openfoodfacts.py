import requests

USER_AGENT = "FitLog-Eksamensprojekt/1.0 (studerende@example.com)"

OFF_SEARCH_A_LICIOUS_URL = "https://search.openfoodfacts.org/search"
OFF_LEGACY_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

LOCAL_FOOD_DATABASE: dict[str, dict[str, float]] = {
    "kylling": {"calories": 165, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6},
    "kyllingebryst": {"calories": 165, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6},
    "kyllingelår": {"calories": 209, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 10.9},
    "oksekød": {"calories": 217, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 12.0},
    "hakket oksekød": {"calories": 217, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 12.0},
    "svinekød": {"calories": 143, "protein_g": 22.0, "carbs_g": 0.0, "fat_g": 5.0},
    "flæsk": {"calories": 376, "protein_g": 14.0, "carbs_g": 0.0, "fat_g": 35.0},
    "bacon": {"calories": 541, "protein_g": 37.0, "carbs_g": 1.4, "fat_g": 42.0},
    "laks": {"calories": 208, "protein_g": 20.0, "carbs_g": 0.0, "fat_g": 13.0},
    "torsk": {"calories": 82, "protein_g": 18.0, "carbs_g": 0.0, "fat_g": 0.7},
    "tun": {"calories": 116, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 1.0},
    "reje": {"calories": 99, "protein_g": 24.0, "carbs_g": 0.2, "fat_g": 0.3},
    "æg": {"calories": 155, "protein_g": 13.0, "carbs_g": 1.1, "fat_g": 11.0},
    "ris": {"calories": 130, "protein_g": 2.7, "carbs_g": 28.0, "fat_g": 0.3},
    "pasta": {"calories": 131, "protein_g": 5.0, "carbs_g": 25.0, "fat_g": 1.1},
    "spaghetti": {"calories": 131, "protein_g": 5.0, "carbs_g": 25.0, "fat_g": 1.1},
    "kartofler": {"calories": 87, "protein_g": 1.9, "carbs_g": 20.0, "fat_g": 0.1},
    "brød": {"calories": 259, "protein_g": 8.5, "carbs_g": 48.0, "fat_g": 1.5},
    "rugbrød": {"calories": 259, "protein_g": 8.5, "carbs_g": 48.0, "fat_g": 1.5},
    "franskbrød": {"calories": 274, "protein_g": 9.0, "carbs_g": 50.0, "fat_g": 3.0},
    "havregryn": {"calories": 389, "protein_g": 13.0, "carbs_g": 66.0, "fat_g": 7.0},
    "mælk": {"calories": 64, "protein_g": 3.4, "carbs_g": 4.8, "fat_g": 3.6},
    "skummetmælk": {"calories": 34, "protein_g": 3.4, "carbs_g": 5.0, "fat_g": 0.1},
    "skyr": {"calories": 63, "protein_g": 11.0, "carbs_g": 4.0, "fat_g": 0.2},
    "yoghurt": {"calories": 61, "protein_g": 3.5, "carbs_g": 4.7, "fat_g": 3.3},
    "ost": {"calories": 403, "protein_g": 25.0, "carbs_g": 1.3, "fat_g": 33.0},
    "smør": {"calories": 717, "protein_g": 0.9, "carbs_g": 0.1, "fat_g": 81.0},
    "olivenolie": {"calories": 884, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 100.0},
    "æble": {"calories": 52, "protein_g": 0.3, "carbs_g": 14.0, "fat_g": 0.2},
    "banan": {"calories": 89, "protein_g": 1.1, "carbs_g": 23.0, "fat_g": 0.3},
    "appelsin": {"calories": 47, "protein_g": 0.9, "carbs_g": 12.0, "fat_g": 0.1},
    "broccoli": {"calories": 34, "protein_g": 2.8, "carbs_g": 7.0, "fat_g": 0.4},
    "gulerod": {"calories": 41, "protein_g": 0.9, "carbs_g": 10.0, "fat_g": 0.2},
    "tomat": {"calories": 18, "protein_g": 0.9, "carbs_g": 3.9, "fat_g": 0.2},
    "agurk": {"calories": 15, "protein_g": 0.7, "carbs_g": 3.6, "fat_g": 0.1},
    "avocado": {"calories": 160, "protein_g": 2.0, "carbs_g": 8.5, "fat_g": 15.0},
    "mandler": {"calories": 579, "protein_g": 21.0, "carbs_g": 22.0, "fat_g": 50.0},
    "jordnøddesmør": {"calories": 588, "protein_g": 25.0, "carbs_g": 20.0, "fat_g": 50.0},
    "linser": {"calories": 116, "protein_g": 9.0, "carbs_g": 20.0, "fat_g": 0.4},
    "kikærter": {"calories": 164, "protein_g": 8.9, "carbs_g": 27.0, "fat_g": 2.6},
    "quinoa": {"calories": 120, "protein_g": 4.4, "carbs_g": 21.0, "fat_g": 1.9},
}

# Sidste udvej hvis hverken den lokale database eller Open Food Facts
# kan finde fødevaren. Svarer nogenlunde til et "gennemsnitligt" måltid.
FALLBACK_PER_100G = {
    "calories": 200.0,
    "protein_g": 8.0,
    "carbs_g": 25.0,
    "fat_g": 7.0,
}


class MacroResult:

    def __init__(
        self,
        calories: float,
        protein_g: float,
        carbs_g: float,
        fat_g: float,
        source: str = "local",
    ):
        self.calories = calories
        self.protein_g = protein_g
        self.carbs_g = carbs_g
        self.fat_g = fat_g
        # "local" | "openfoodfacts" | "fallback" - bruges af frontenden
        # til at vise brugeren hvor sikkert tallet er.
        self.source = source


def _normalize(text: str) -> str:
    return text.strip().lower()


def _lookup_local(food_name: str) -> dict[str, float] | None:
  
    query = _normalize(food_name)

    if query in LOCAL_FOOD_DATABASE:
        return LOCAL_FOOD_DATABASE[query]

    matches = [key for key in LOCAL_FOOD_DATABASE if key in query or query in key]
    if not matches:
        return None

    best_match = max(matches, key=len)
    return LOCAL_FOOD_DATABASE[best_match]


def _parse_off_nutriments(nutriments: dict) -> dict[str, float] | None:
    calories = nutriments.get("energy-kcal_100g")
    if calories is None:
        return None
    return {
        "calories": calories,
        "protein_g": nutriments.get("proteins_100g", 0.0),
        "carbs_g": nutriments.get("carbohydrates_100g", 0.0),
        "fat_g": nutriments.get("fat_100g", 0.0),
    }


def _lookup_openfoodfacts(food_name: str) -> dict[str, float] | None:
   
    headers = {"User-Agent": USER_AGENT}

    sal_params: dict[str, str | int] = {"q": food_name, "page_size": 1, "langs": "da,en"}
    try:
        response = requests.get(
            OFF_SEARCH_A_LICIOUS_URL,
            params=sal_params,
            headers=headers,
            timeout=5,
        )
        if response.ok:
            hits = response.json().get("hits", [])
            if hits:
                result = _parse_off_nutriments(hits[0].get("nutriments", {}))
                if result:
                    return result
    except (requests.RequestException, ValueError):
        pass

    legacy_params: dict[str, str | int] = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 1,
    }
    try:
        response = requests.get(
            OFF_LEGACY_SEARCH_URL,
            params=legacy_params,
            headers=headers,
            timeout=5,
        )
        if response.ok:
            products = response.json().get("products", [])
            if products:
                result = _parse_off_nutriments(products[0].get("nutriments", {}))
                if result:
                    return result
    except (requests.RequestException, ValueError):
        pass

    return None


def calculate_macros(food_name: str, grams: float) -> MacroResult:
   
    per_100g = _lookup_local(food_name)
    source = "local"

    if per_100g is None:
        per_100g = _lookup_openfoodfacts(food_name)
        source = "openfoodfacts"

    if per_100g is None:
        per_100g = FALLBACK_PER_100G
        source = "fallback"

    factor = grams / 100.0

    return MacroResult(
        calories=round(per_100g["calories"] * factor, 1),
        protein_g=round(per_100g["protein_g"] * factor, 1),
        carbs_g=round(per_100g["carbs_g"] * factor, 1),
        fat_g=round(per_100g["fat_g"] * factor, 1),
        source=source,
    )
