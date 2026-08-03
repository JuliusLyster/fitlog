"""
Unittests for app/services/openfoodfacts.py

Tester tre-trins-strategien: lokal database -> Open Food Facts -> fallback.
HTTP-kald mockes, så testene ikke er afhængige af at det eksterne API
rent faktisk svarer (hvilket det ifølge egne erfaringer ikke altid gør).
"""

from unittest.mock import Mock, patch

import requests

from app.services.openfoodfacts import (
    FALLBACK_PER_100G,
    OFF_SEARCH_A_LICIOUS_URL,
    calculate_macros,
)


def test_local_database_gives_different_values_per_food():
    """Regressionstest for buggen hvor alle fødevarer gav samme makroer."""
    kylling = calculate_macros("kylling", 100)
    ris = calculate_macros("ris", 100)
    bacon = calculate_macros("bacon", 100)

    values = {kylling.calories, ris.calories, bacon.calories}
    assert len(values) == 3, "Forskellige fødevarer skal give forskellige kalorietal"

    assert kylling.source == "local"
    assert ris.source == "local"
    assert bacon.source == "local"


def test_local_database_scales_by_grams():
    result = calculate_macros("kylling", 200)

    # Kylling: 165 kcal / 31g protein pr. 100g -> 200g = 2x
    assert result.calories == 330.0
    assert result.protein_g == 62.0
    assert result.source == "local"


def test_local_database_partial_match():
    """'Stegt kylling i ovn' skal stadig matche 'kylling' i databasen."""
    result = calculate_macros("stegt kylling i ovn", 100)
    assert result.source == "local"
    assert result.calories == 165.0


def test_local_database_is_case_insensitive():
    result = calculate_macros("KYLLING", 100)
    assert result.source == "local"
    assert result.calories == 165.0


def test_unknown_food_falls_through_to_openfoodfacts():
    fake_response = Mock()
    fake_response.ok = True
    fake_response.json.return_value = {
        "hits": [
            {
                "nutriments": {
                    "energy-kcal_100g": 250,
                    "proteins_100g": 12,
                    "carbohydrates_100g": 30,
                    "fat_100g": 8,
                }
            }
        ]
    }

    with patch("app.services.openfoodfacts.requests.get", return_value=fake_response):
        result = calculate_macros("et helt ukendt produkt", 100)

    assert result.source == "openfoodfacts"
    assert result.calories == 250.0


def test_openfoodfacts_falls_back_to_legacy_search_if_search_a_licious_fails():
    fake_legacy_response = Mock()
    fake_legacy_response.ok = True
    fake_legacy_response.json.return_value = {
        "products": [
            {
                "nutriments": {
                    "energy-kcal_100g": 180,
                    "proteins_100g": 9,
                    "carbohydrates_100g": 22,
                    "fat_100g": 6,
                }
            }
        ]
    }

    def fake_get(url, *args, **kwargs):
        if url == OFF_SEARCH_A_LICIOUS_URL:
            raise requests.RequestException("search-a-licious er nede")
        return fake_legacy_response

    with patch("app.services.openfoodfacts.requests.get", side_effect=fake_get):
        result = calculate_macros("et helt ukendt produkt", 100)

    assert result.source == "openfoodfacts"
    assert result.calories == 180.0


def test_unknown_food_uses_fallback_when_all_sources_fail():
    with patch(
        "app.services.openfoodfacts.requests.get",
        side_effect=requests.RequestException("nede"),
    ):
        result = calculate_macros("et helt ukendt produkt", 100)

    assert result.source == "fallback"
    assert result.calories == FALLBACK_PER_100G["calories"]


def test_zero_grams_gives_zero_macros():
    result = calculate_macros("kylling", 0)
    assert result.calories == 0.0
