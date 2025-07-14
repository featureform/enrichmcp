from enrichmcp.context import (
    prefer_fast_model,
    prefer_medium_model,
    prefer_smart_model,
)


def test_model_preference_helpers():
    fast = prefer_fast_model()
    medium = prefer_medium_model()
    smart = prefer_smart_model()

    assert fast.speedPriority > fast.costPriority
    assert medium.speedPriority > medium.costPriority
    assert smart.intelligencePriority > smart.speedPriority
