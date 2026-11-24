from __future__ import annotations

import unittest
from unittest.mock import patch

try:
    from .helpers import RocoTestCase
except ImportError:
    from helpers import RocoTestCase

from roco_serverchan_notifier import app as app_module
from roco_serverchan_notifier.push import DeliveryReport, PushResult


class AppTests(RocoTestCase):
    def test_run_once_returns_no_report_when_empty_is_skipped(self):
        settings = self.make_settings(notify_empty=True)

        with patch.object(app_module, "fetch_merchant_data", return_value={"merchantActivities": []}), patch.object(
            app_module, "send_delivery"
        ) as send_mock:
            result = app_module.run_once(settings)

        send_mock.assert_not_called()

        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(result.report)

    def test_each_watched_product_triggers_delivery_of_full_list(self):
        settings = self.make_settings()
        report = DeliveryReport(True, "all", [PushResult("p1", "通道", "serverchan", True, "ok")])

        for target in ("国王球", "炫彩精灵蛋", "祝福项坠"):
            with self.subTest(target=target):
                raw_data = {"merchantActivities": [{"get_props": [{"name": "咕噜球"}, {"name": target}]}]}
                with patch.object(app_module, "fetch_merchant_data", return_value=raw_data), patch.object(
                    app_module, "send_delivery", return_value=report
                ) as send_mock:
                    result = app_module.run_once(settings)

                self.assertEqual(result.exit_code, 0)
                self.assertIs(result.report, report)
                self.assertIn(target, send_mock.call_args.args[1].markdown)
                self.assertIn("咕噜球", send_mock.call_args.args[1].markdown)

    def test_nonmatching_and_expired_products_do_not_trigger_delivery(self):
        raw_data = {"merchantActivities": [{"get_props": [
            {"name": "咕噜球"},
            {"name": "国王球礼包"},
            {"name": "国王球", "start_time": 1000, "end_time": 2000},
        ]}]}
        with patch.object(app_module, "fetch_merchant_data", return_value=raw_data), patch.object(
            app_module, "send_delivery"
        ) as send_mock:
            result = app_module.run_once(self.make_settings())

        self.assertEqual(result.exit_code, 0)
        send_mock.assert_not_called()

    def test_data_fetch_failure_does_not_trigger_delivery(self):
        with patch.object(app_module, "fetch_merchant_data", side_effect=RuntimeError("接口错误")), patch.object(
            app_module, "send_delivery"
        ) as send_mock:
            result = app_module.run_once(self.make_settings())

        self.assertEqual(result.exit_code, 1)
        self.assertIsNone(result.report)
        send_mock.assert_not_called()

    def test_push_uses_configured_timeout(self):
        settings = self.make_settings(http_timeout=42, notify_empty=True)
        raw_data = {
            "merchantActivities": [
                {
                    "name": "远行商人",
                    "get_props": [{"name": "国王球"}],
                    "get_pets": [],
                }
            ]
        }

        with patch.object(app_module, "fetch_merchant_data", return_value=raw_data), patch.object(
            app_module,
            "send_delivery",
            return_value=DeliveryReport(True, "all", []),
        ) as send_mock:
            exit_code = app_module.run_once(settings)

        self.assertEqual(exit_code, 0)
        self.assertEqual(send_mock.call_args.kwargs["options"].timeout, 42)


if __name__ == "__main__":
    unittest.main()
