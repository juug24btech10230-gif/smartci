import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from depgraph import build_graph, reverse_graph  # noqa: E402
from select_tests import select  # noqa: E402
from smart_cache import module_keys  # noqa: E402
from summarize_log import rule_based_summary, trim_log  # noqa: E402


def test_graph_cart_depends_on_pricing():
    assert "pricing" in build_graph()["cart"]
    assert "cart" in reverse_graph(build_graph())["pricing"]


def test_routing_pricing_change_selects_cart_and_pricing():
    tests, _ = select(["src/pricing.py"])
    assert tests == ["tests/test_cart.py", "tests/test_pricing.py"]


def test_routing_inventory_change_is_isolated():
    tests, _ = select(["src/inventory.py"])
    assert tests == ["tests/test_inventory.py"]


def test_routing_config_runs_everything():
    tests, _ = select(["requirements.txt"])
    assert len(tests) == 4  # includes this file


def test_cache_keys_stable_and_distinct():
    a, b = module_keys(), module_keys()
    assert a == b
    assert len(set(a.values())) == len(a)


def test_summary_detects_failure():
    log = "FAILED tests/test_pricing.py::test_discount_basic\nE   assert 90.0 == 91.0\n1 failed, 8 passed"
    assert "1 test(s) failed" in rule_based_summary(log)
    assert "assert 90.0 == 91.0" in trim_log(log)
