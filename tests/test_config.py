from engine import config


def test_blocking_thresholds_ordered():
    r = config.ROUTING
    assert 0 < r.block_vehicle < r.block_offline < r.block_walk <= 1


def test_level_weights_increase():
    w = config.RISK.level_weight
    assert w["ankle"] < w["knee"] < w["waist"] < w["above"] <= 1


def test_export_has_routing_thresholds():
    assert config.export()["routing"]["block_walk"] == config.ROUTING.block_walk
