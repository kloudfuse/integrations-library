"""Check the library, or rebuild dist/ from integrations/.

Usage:
  python3 scripts/validate.py          # report problems, exit 1 if any
  python3 scripts/validate.py --write  # clean the sources, regenerate dist/, then check
"""

import json
import sys
from pathlib import Path

COLLECTORS = ("otel", "datadog", "cloud")
RULE_FIELDS = ("title", "condition", "data", "noDataState", "execErrState")
# Fields a Grafana export carries that belong to the instance it came from, not the library.
DASHBOARD_INSTANCE_FIELDS = ("id", "uid", "version", "__inputs")
RULE_INSTANCE_FIELDS = ("id", "uid", "orgId", "folderUID", "ruleGroup", "updated", "provenance")
# Installs save dashboards without Grafana's import step, so an export's ${DS_*} would never be filled in.
PLACEHOLDER = "${DS_"
PROMETHEUS_UID = "P09C4D52DEC9B98E6"
DATASOURCE_UIDS = {None: PROMETHEUS_UID, "prometheus": PROMETHEUS_UID, "loki": "P10239062BE9ED4EF", "__expr__": "__expr__"}
STALE = "dist/ is out of date; run scripts/validate.py --write"


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except ValueError as exc:
        return None, f"{path}: not valid JSON ({exc})"


def _folders(root: Path) -> list[Path]:
    return sorted(p for p in (root / "integrations").glob("*/*") if p.is_dir())


def _id(folder: Path) -> str:
    return f"{folder.parent.name}-{folder.name}"


def _json_files(folder: Path, sub: str) -> list[Path]:
    return sorted((folder / sub).glob("*.json"))


def _strip(obj: dict, fields) -> dict:
    return {k: v for k, v in obj.items() if k not in fields}


def _resolve_datasources(node):
    if isinstance(node, list):
        return [_resolve_datasources(item) for item in node]
    if not isinstance(node, dict):
        return node
    out = {key: _resolve_datasources(value) for key, value in node.items()}
    ds = out.get("datasource")
    if isinstance(ds, dict) and str(ds.get("uid", "")).startswith(PLACEHOLDER) and ds.get("type") in DATASOURCE_UIDS:
        out["datasource"] = {**ds, "uid": DATASOURCE_UIDS[ds.get("type")]}
    return out


def _clean_dashboard(dash):
    return _resolve_datasources(_strip(dash, DASHBOARD_INSTANCE_FIELDS)) if isinstance(dash, dict) else dash


def _clean_group(group):
    if not isinstance(group, dict) or not isinstance(group.get("rules"), list):
        return group
    rules = [_strip(r, RULE_INSTANCE_FIELDS) if isinstance(r, dict) else r for r in group["rules"]]
    return {**group, "rules": rules}


def _package(folder: Path) -> dict:
    meta, _ = _load(folder / "metadata.json")
    meta = meta if isinstance(meta, dict) else {}
    details = folder / "DESCRIPTION.md"
    return {
        "schemaVersion": 1,
        "id": _id(folder),
        "name": meta.get("name"),
        "collector": meta.get("collector"),
        "tags": meta.get("tags"),
        "description": meta.get("summary"),
        "details": details.read_text(encoding="utf-8") if details.exists() else "",
        "dashboards": [_clean_dashboard(_load(p)[0]) for p in _json_files(folder, "dashboards")],
        "alerts": [_clean_group(_load(p)[0]) for p in _json_files(folder, "alerts")],
    }


def _index_entry(pkg: dict) -> dict:
    dashboards = [d.get("title", "") for d in pkg["dashboards"] if isinstance(d, dict)]
    rules = [r.get("title", "") for g in pkg["alerts"] if isinstance(g, dict) for r in g.get("rules", [])
             if isinstance(r, dict)]
    return {
        "id": pkg["id"],
        "name": pkg["name"],
        "collector": pkg["collector"],
        "tags": pkg["tags"],
        "description": pkg["description"],
        "details": pkg["details"],
        "path": f"{pkg['id']}.json",
        "dashboards": dashboards,
        "alerts": rules,
    }


def build(root: Path) -> dict[str, str]:
    """Every dist/ file's name and exact text."""
    packages = [_package(folder) for folder in _folders(root)]
    out = {f"{pkg['id']}.json": json.dumps(pkg, separators=(",", ":"), ensure_ascii=False) + "\n" for pkg in packages}
    index = {"schemaVersion": 1, "integrations": [_index_entry(pkg) for pkg in packages]}
    out["index.json"] = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    return out


def _folder_problems(folder: Path, allowed_tags: list[str]) -> list[str]:
    where = f"integrations/{folder.parent.name}/{folder.name}"
    iid = _id(folder)
    out = []
    if folder.name not in COLLECTORS:
        out.append(f"{where}: collector must be one of {', '.join(COLLECTORS)}")

    meta, error = _load(folder / "metadata.json") if (folder / "metadata.json").exists() else (None, f"{where}: metadata.json is missing")
    if error:
        out.append(error)
    elif not isinstance(meta, dict):
        out.append(f"{where}: metadata.json must be a JSON object")
    else:
        if meta.get("schemaVersion") != 1:
            out.append(f"{where}: metadata.json schemaVersion must be 1")
        if meta.get("collector") != folder.name:
            out.append(f"{where}: collector {meta.get('collector')!r} does not match its folder")
        for key in ("name", "summary"):
            if not isinstance(meta.get(key), str) or not meta[key].strip():
                out.append(f"{where}: {key} must be a non-empty string")
        tags = meta.get("tags")
        if not isinstance(tags, list) or not tags:
            out.append(f"{where}: tags must be a non-empty list")
        else:
            out.extend(f"{where}: tag {t!r} is not in tags.json" for t in tags if t not in allowed_tags)

    details = folder / "DESCRIPTION.md"
    if not details.exists():
        out.append(f"{where}: DESCRIPTION.md is missing")
    elif not details.read_text(encoding="utf-8").strip():
        out.append(f"{where}: DESCRIPTION.md is empty")

    for path in _json_files(folder, "dashboards"):
        dash, error = _load(path)
        if error:
            out.append(error)
            continue
        name = f"{where}/dashboards/{path.name}"
        if not isinstance(dash, dict) or not isinstance(dash.get("title"), str) or not isinstance(dash.get("panels"), list):
            out.append(f"{name}: needs a title and a panels list")
        elif dash != _clean_dashboard(dash):
            out.append(f"{name}: has instance fields; run scripts/validate.py --write")
        elif PLACEHOLDER in json.dumps(dash):
            out.append(f"{name}: has a {PLACEHOLDER}...}} datasource placeholder with no known Kloudfuse UID")

    for path in _json_files(folder, "alerts"):
        group, error = _load(path)
        if error:
            out.append(error)
            continue
        name = f"{where}/alerts/{path.name}"
        if not isinstance(group, dict) or not isinstance(group.get("name"), str) or not isinstance(group.get("rules"), list):
            out.append(f"{name}: a rule group needs a name and a rules list")
            continue
        if group["name"] != path.stem:
            out.append(f"{name}: group name {group['name']!r} does not match its filename")
        if group["name"] != iid and not group["name"].startswith(f"{iid}-"):
            out.append(f"{name}: group name must be {iid!r} or start with {iid + '-'!r}")
        for r in group["rules"]:
            if not isinstance(r, dict):
                out.append(f"{name}: each rule must be a JSON object")
                continue
            title = r.get("title") or r.get("grafana_alert", {}).get("title", "?")
            if "grafana_alert" in r:
                out.append(f"{name}: rule {title!r} is in Grafana's ruler shape; use the provisioning-export shape")
                continue
            missing = [f for f in RULE_FIELDS if f not in r]
            if missing:
                out.append(f"{name}: rule {title!r} is missing {', '.join(missing)}")
        if group != _clean_group(group):
            out.append(f"{name}: has instance fields; run scripts/validate.py --write")
    return out


def _allowed_tags(root: Path) -> tuple[list[str], list[str]]:
    tags, error = _load(root / "tags.json") if (root / "tags.json").exists() else (None, "tags.json is missing")
    if error:
        return [], [error]
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return [], ["tags.json must be a list of strings"]
    return tags, []


def problems(root: Path) -> list[str]:
    allowed, out = _allowed_tags(root)
    for folder in _folders(root):
        out.extend(_folder_problems(folder, allowed))
    if out:
        return out
    dist = root / "dist"
    current = {p.name: p.read_text(encoding="utf-8") for p in dist.glob("*")} if dist.is_dir() else {}
    if current != build(root):
        out.append(STALE)
    return out


def write(root: Path) -> None:
    """Strip instance fields from the sources, then regenerate dist/ to match them."""
    for folder in _folders(root):
        for sub, clean in (("dashboards", _clean_dashboard), ("alerts", _clean_group)):
            for path in _json_files(folder, sub):
                obj, error = _load(path)
                if not error and clean(obj) != obj:
                    path.write_text(json.dumps(clean(obj), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    files = build(root)
    for stale in dist.glob("*"):
        if stale.name not in files:
            stale.unlink()
    for name, text in files.items():
        (dist / name).write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    if "--write" in argv:
        write(root)
    found = problems(root)
    for line in found:
        print(line)
    print(f"{len(_folders(root))} integrations, {len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
