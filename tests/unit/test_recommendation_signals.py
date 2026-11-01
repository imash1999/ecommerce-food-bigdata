from scripts.spark.recommendation_signals import BEHAVIOR_WEIGHTS


def test_behavior_event_weights():
    assert BEHAVIOR_WEIGHTS == {
        "view": 1.0,
        "add_to_cart": 3.0,
        "buy": 5.0,
    }
