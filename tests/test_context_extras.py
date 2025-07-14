from enrichmcp.context import prefer_fast_model, prefer_smart_model


def test_prefer_fast_and_smart_models():
    fast = prefer_fast_model()
    smart = prefer_smart_model()
    assert fast.speedPriority > fast.costPriority
    assert smart.intelligencePriority > smart.speedPriority
