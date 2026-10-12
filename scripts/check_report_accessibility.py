"""Structural accessibility checks; not a screen-reader or full WCAG certificate."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def contrast(a, b):
    def luminance(color):
        values = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(w * v for w, v in zip([0.2126, 0.7152, 0.0722], values, strict=True))

    bright, dark = sorted([luminance(a), luminance(b)], reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def check(root=ROOT):
    folder = root / "powerbi/report"
    pages = list((folder / "definition/pages").glob("*/page.json"))
    count = 0
    for page in pages:
        visuals = [json.loads(p.read_text()) for p in page.parent.glob("visuals/*/visual.json")]
        ordered = sorted(visuals, key=lambda v: (v["position"]["y"], v["position"]["x"]))
        if [v["position"]["tabOrder"] for v in ordered] != list(range(len(ordered))):
            raise ValueError("Reading order differs from visible layout")
        for visual in visuals:
            literal = visual["visual"]["visualContainerObjects"]["general"][0]["properties"][
                "altText"
            ]["expr"]["Literal"]["Value"]
            if not 3 <= len(literal) <= 252:
                raise ValueError("Missing or overlong alt text")
            if (
                visual["visual"]["visualType"] == "lineChart"
                and visual["visual"]
                .get("objects", {})
                .get("lineStyles", [{}])[0]
                .get("properties", {})
                .get("showMarker", {})
                .get("expr", {})
                .get("Literal", {})
                .get("Value")
                != "true"
            ):
                raise ValueError("Line-chart markers missing")
            count += 1
    theme = json.loads(next(folder.glob("StaticResources/RegisteredResources/*.json")).read_text())
    for color in theme["dataColors"]:
        if contrast(color, "#FFFFFF") < 3:
            raise ValueError("Chart color below 3:1 against white: " + color)
    if contrast(theme["foreground"], "#FFFFFF") < 4.5:
        raise ValueError("Foreground text contrast below 4.5:1")
    return dict(
        status="passed",
        pages=len(pages),
        visuals=count,
        checks=["alt text", "layout reading order", "line markers", "palette contrast"],
        limits="Theme-level white-background contrast, not every rendered text/background pair; screen-reader and color-vision user review remain outstanding.",
    )


if __name__ == "__main__":
    result = check()
    (ROOT / "build/report-accessibility.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
