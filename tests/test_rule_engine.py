from ai_grain_grade.rule_engine import RagiRuleEngine


BASE_PROXIES = {
    "lab_features": {"color_darkness_index": 35.0},
    "clumping": {"density": 0.05},
    "uniformity_score": 82.0,
    "roughness_score": 45.0,
    "grain_mask_coverage": 0.45,
}


def test_grade_a_requires_premium_fao_bis_thresholds():
    engine = RagiRuleEngine()
    decision = engine.evaluate(
        {
            "quality_grade": "A",
            "off_tone_fraction": 2.0,
            "size_deviation": 2.0,
            "shape_defect_fraction": 2.0,
            "broken_grain_percent": 1.0,
            "foreign_matter_percent": 0.05,
            "other_edible_grains_percent": 0.2,
            "bimodal_color_detected": False,
            "mold_visible": False,
            "visible_defects": [],
        },
        BASE_PROXIES,
        moisture_risk="LOW",
        moisture_percent=11.5,
    )

    assert decision.grade == "A"
    assert decision.reject is False


def test_moisture_above_outer_ragi_range_rejects():
    engine = RagiRuleEngine()
    decision = engine.evaluate(
        {
            "quality_grade": "A",
            "off_tone_fraction": 2.0,
            "size_deviation": 2.0,
            "shape_defect_fraction": 2.0,
            "broken_grain_percent": 1.0,
            "foreign_matter_percent": 0.05,
            "bimodal_color_detected": False,
            "mold_visible": False,
        },
        BASE_PROXIES,
        moisture_risk="CRITICAL",
        moisture_percent=14.5,
    )

    assert decision.grade == "C"
    assert decision.reject is True
    assert "moisture_reject" in decision.rule_hits


def test_foreign_matter_cannot_pass_outer_threshold():
    engine = RagiRuleEngine()
    decision = engine.evaluate(
        {
            "quality_grade": "B",
            "foreign_matter_percent": 1.2,
            "broken_grain_percent": 1.0,
            "shape_defect_fraction": 2.0,
            "mold_visible": False,
        },
        BASE_PROXIES,
        moisture_risk="LOW",
        moisture_percent=11.5,
    )

    assert decision.grade == "C"
    assert decision.reject is True
    assert "foreign_matter_reject" in decision.rule_hits
