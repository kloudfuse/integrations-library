"""Tests for scripts/validate.py. Run: python3 -m unittest discover tests"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate  # noqa: E402


def rule(**overrides):
    out = {
        "title": "Redis down",
        "condition": "B",
        "data": [],
        "noDataState": "OK",
        "execErrState": "KeepLast",
        "for": "5m",
        "annotations": {},
        "labels": {},
    }
    out.update(overrides)
    return out


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "tags.json").write_text(json.dumps(["cache", "database"]))

    def tearDown(self):
        self.tmp.cleanup()

    def integration(self, component="redis", collector="datadog", metadata=None, description="Redis keyspace metrics.\n",
                    dashboards=None, alerts=None):
        folder = self.root / "integrations" / component / collector
        (folder / "dashboards").mkdir(parents=True)
        (folder / "alerts").mkdir()
        meta = {"schemaVersion": 1, "name": "Redis", "summary": "Redis keyspace metrics.", "collector": collector,
                "tags": ["cache"]}
        meta.update(metadata or {})
        (folder / "metadata.json").write_text(json.dumps(meta))
        if description is not None:
            (folder / "DESCRIPTION.md").write_text(description)
        if dashboards is None:
            dashboards = {"overview.json": {"title": "Redis - Overview", "panels": []}}
        for name, dash in dashboards.items():
            (folder / "dashboards" / name).write_text(dash if isinstance(dash, str) else json.dumps(dash))
        if alerts is None:
            alerts = {f"{component}-{collector}.json": {"name": f"{component}-{collector}", "interval": "1m",
                                                        "rules": [rule()]}}
        for name, group in alerts.items():
            (folder / "alerts" / name).write_text(json.dumps(group))
        return folder

    def problems_after_write(self):
        validate.write(self.root)
        return validate.problems(self.root)

    def dist(self, name):
        return json.loads((self.root / "dist" / name).read_text())

    def test_valid_library_has_no_problems(self):
        self.integration()
        self.assertEqual(self.problems_after_write(), [])

    def test_dist_package_combines_the_source_folder(self):
        self.integration(dashboards={
            "b.json": {"title": "Second", "panels": []},
            "a.json": {"title": "First", "panels": []},
        })
        validate.write(self.root)
        pkg = self.dist("redis-datadog.json")
        self.assertEqual(pkg["id"], "redis-datadog")
        self.assertEqual(pkg["collector"], "datadog")
        self.assertEqual(pkg["tags"], ["cache"])
        self.assertEqual(pkg["description"], "Redis keyspace metrics.")
        self.assertEqual(pkg["details"], "Redis keyspace metrics.\n")
        self.assertEqual([d["title"] for d in pkg["dashboards"]], ["First", "Second"])
        self.assertEqual(pkg["alerts"][0]["rules"][0]["title"], "Redis down")

    def test_index_lists_titles_and_tags(self):
        self.integration()
        validate.write(self.root)
        entry = self.dist("index.json")["integrations"][0]
        self.assertEqual(entry["path"], "redis-datadog.json")
        self.assertEqual(entry["tags"], ["cache"])
        self.assertEqual(entry["details"], "Redis keyspace metrics.\n")
        self.assertEqual(entry["dashboards"], ["Redis - Overview"])
        self.assertEqual(entry["alerts"], ["Redis down"])

    def test_stale_dist_is_a_problem(self):
        self.integration()
        validate.write(self.root)
        self.integration(component="kafka", alerts={})
        self.assertIn("dist/ is out of date; run scripts/validate.py --write", validate.problems(self.root))

    def test_dist_file_for_a_removed_integration_is_a_problem(self):
        self.integration()
        validate.write(self.root)
        (self.root / "dist" / "gone-datadog.json").write_text("{}")
        self.assertIn("dist/ is out of date; run scripts/validate.py --write", validate.problems(self.root))

    def test_write_removes_stale_dist_files(self):
        self.integration()
        (self.root / "dist").mkdir()
        (self.root / "dist" / "gone-datadog.json").write_text("{}")
        validate.write(self.root)
        self.assertFalse((self.root / "dist" / "gone-datadog.json").exists())

    def test_collector_must_match_its_folder(self):
        self.integration(metadata={"collector": "otel"})
        self.assertTrue(any("does not match its folder" in p for p in self.problems_after_write()))

    def test_unknown_collector_folder(self):
        self.integration(collector="newrelic", metadata={"collector": "newrelic"})
        self.assertTrue(any("collector must be one of" in p for p in self.problems_after_write()))

    def test_unknown_tag(self):
        self.integration(metadata={"tags": ["Cache"]})
        self.assertTrue(any("'Cache' is not in tags.json" in p for p in self.problems_after_write()))

    def test_tags_must_not_be_empty(self):
        self.integration(metadata={"tags": []})
        self.assertTrue(any("tags must be a non-empty list" in p for p in self.problems_after_write()))

    def test_missing_description_file(self):
        self.integration(description=None)
        self.assertTrue(any("DESCRIPTION.md is missing" in p for p in validate.problems(self.root)))

    def test_ruler_shape_rule_is_rejected(self):
        ruler = {"expr": "", "for": "5m", "grafana_alert": {"title": "x"}}
        self.integration(alerts={"redis-datadog.json": {"name": "redis-datadog", "interval": "1m", "rules": [ruler]}})
        self.assertTrue(any("ruler shape" in p for p in self.problems_after_write()))

    def test_group_name_must_start_with_the_integration_id(self):
        self.integration(alerts={"redis.json": {"name": "redis", "interval": "1m", "rules": [rule()]}})
        self.assertTrue(any("must be 'redis-datadog' or start with 'redis-datadog-'" in p
                            for p in self.problems_after_write()))

    def test_group_name_must_match_its_filename(self):
        self.integration(alerts={"other.json": {"name": "redis-datadog", "interval": "1m", "rules": [rule()]}})
        self.assertTrue(any("does not match its filename" in p for p in self.problems_after_write()))

    def test_dashboard_needs_title_and_panels(self):
        self.integration(dashboards={"x.json": {"title": "x"}})
        self.assertTrue(any("needs a title and a panels list" in p for p in self.problems_after_write()))

    def test_invalid_json(self):
        self.integration(dashboards={"broken.json": "{ nope"})
        self.assertTrue(any("not valid JSON" in p for p in validate.problems(self.root)))

    def test_write_strips_instance_fields_from_the_source(self):
        folder = self.integration(
            dashboards={"overview.json": {"id": 7, "uid": "abc", "version": 3, "title": "Redis", "panels": []}},
            alerts={"redis-datadog.json": {"name": "redis-datadog", "interval": "1m",
                                           "rules": [rule(uid="u", id=4, orgId=1, folderUID="f", ruleGroup="g",
                                                          updated="t", provenance="api")]}},
        )
        self.assertTrue(any("instance fields" in p for p in validate.problems(self.root)))
        validate.write(self.root)
        dash = json.loads((folder / "dashboards" / "overview.json").read_text())
        written = json.loads((folder / "alerts" / "redis-datadog.json").read_text())["rules"][0]
        self.assertEqual(sorted(dash), ["panels", "title"])
        self.assertEqual(sorted(set(written) & {"uid", "id", "orgId", "folderUID", "ruleGroup", "updated", "provenance"}),
                         [])
        self.assertEqual(validate.problems(self.root), [])


if __name__ == "__main__":
    unittest.main()
