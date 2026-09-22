"""直接提取文档中的 Python 代码，避免另存一份示例后内容不一致。"""

from copy import deepcopy
from pathlib import Path
import re
import sys
import types
import unittest


PAGE = Path(__file__).resolve().parents[2] / "docs/specification/device-integration/python-example.mdx"
source = "\n\n".join(re.findall(r"```python\n(.*?)\n```", PAGE.read_text(), re.S))
example = types.ModuleType("documented_adapter")
sys.modules[example.__name__] = example
exec(compile(source, str(PAGE), "exec"), example.__dict__)


class DocumentedAdapterTests(unittest.TestCase):
    def setUp(self):
        self.device = example.Device("device-01", {"liquid_transfer"}, ready=True)
        decimal = example.Decimal
        self.objects = {
            "source": example.Container("source-01", "source", "source-8", decimal("10"), decimal("100")),
            "target": example.Container("container-01", "target", "object-21", decimal("0"), decimal("45")),
        }
        self.expected = {"source": "source-8", "target": "object-21"}
        self.operation = {"operation_id": "add_liquid", "contract_version": "1",
                          "parameters": {"volume_mL": 0.5}}
        self.driver = example.SimulatedDriver()
        self.adapter = example.LiquidAdapter("device-01", example.ADD_LIQUID, self.driver)
        self.bindings = {("device-01", "add_liquid", "1"): self.adapter}

    def execute(self, allowed=True):
        return example.execute_once(example.ADD_LIQUID, self.device, self.bindings,
                                    self.operation, self.objects, self.expected, allowed)

    def assert_rejected(self, code, allowed=True):
        with self.assertRaisesRegex(example.Rejected, code):
            self.execute(allowed)
        self.assertEqual(self.driver.calls, 0)

    def test_complete_example(self):
        result = self.execute()
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["actual_volume_mL"], 0.498)
        self.assertTrue(result["simulated"])
        self.assertEqual(self.driver.calls, 1)
        self.assertTrue(all(obj.volume_ml is None for obj in self.objects.values()))

    def test_parameter_validation(self):
        for value in [True, "0.5", float("nan"), float("inf"), -1, 0.9, 0.0501]:
            with self.subTest(value=value):
                self.operation["parameters"]["volume_mL"] = value
                with self.assertRaises(example.Rejected):
                    self.execute()
        self.assertEqual(self.driver.calls, 0)

    def test_wrong_version(self):
        self.operation["contract_version"] = "2"
        self.assert_rejected("unsupported_version")

    def test_permission(self):
        self.assert_rejected("authorization_denied", allowed=False)

    def test_hardware_support(self):
        self.device.capabilities.clear()
        self.assert_rejected("capability_missing")

    def test_missing_binding(self):
        self.bindings.clear()
        self.assert_rejected("implementation_missing")

    def test_wrong_device_binding(self):
        self.adapter.device_id = "other-device"
        self.assert_rejected("implementation_missing")

    def test_readiness(self):
        self.device.ready = False
        self.assert_rejected("action_not_ready")

    def test_busy(self):
        self.device.busy = True
        self.assert_rejected("resource_busy")

    def test_source_revision(self):
        self.expected["source"] = "source-7"
        self.assert_rejected("revision_conflict")

    def test_target_capacity(self):
        self.objects["target"].capacity_ml = example.Decimal("0.1")
        self.assert_rejected("capacity_insufficient")

    def test_target_closed(self):
        self.objects["target"].is_open = False
        self.assert_rejected("object_state_conflict")

    def test_ack_is_not_completion(self):
        self.driver.dose_ul = lambda value: {"ack": True}
        result = self.execute()
        self.assertEqual(result["status"], "unknown")
        self.assertTrue(self.device.needs_review)

    def test_lost_reply_blocks_next_action(self):
        self.driver.lose_reply = True
        result = self.execute()
        self.assertEqual(result["status"], "unknown")
        self.assertTrue(self.device.needs_review)
        self.assertEqual(self.driver.calls, 1)
        self.assertLess(self.driver.source_ul, 10000)
        with self.assertRaisesRegex(example.Rejected, "result_unknown"):
            self.execute()
        self.assertEqual(self.driver.calls, 1)

    def test_out_of_tolerance_preserves_actual_result(self):
        self.driver.dose_ul = lambda value: {"stopped": True, "delivered_ul": 400}
        result = self.execute()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["actual_volume_mL"], 0.4)
        self.assertTrue(all(obj.volume_ml is None for obj in self.objects.values()))

    def test_input_not_modified(self):
        before = deepcopy(self.operation)
        self.execute()
        self.assertEqual(self.operation, before)


if __name__ == "__main__":
    unittest.main()
