"""Generate evidence charts, a one-page PDF and narrated-video slide assets.

These are independently rendered figures, never Power BI screenshots.
"""

import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assets"
OUT.mkdir(exist_ok=True)


def read(name):
    return json.loads((ROOT / "evidence" / f"{name}.json").read_text())


facts = json.loads((ROOT / "build/run/tables.json").read_text())["FactOps"]
summary = read("summary")
decision = read("decisions")
pilot = read("pilot")
diag = read("diagnostics")
planning = read("pilot-planning")
sens = read("sensitivity")
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.facecolor": "white",
        "figure.facecolor": "#F3F6F8",
        "text.color": "#102A43",
        "axes.labelcolor": "#102A43",
        "savefig.facecolor": "#F3F6F8",
    }
)


def figure(title):
    fig, ax = plt.subplots(figsize=(12, 6.75), dpi=130)
    fig.subplots_adjust(left=0.20, right=0.94, bottom=0.18, top=0.79)
    fig.text(0.06, 0.9, title, fontsize=22, fontweight="bold")
    fig.text(
        0.06,
        0.045,
        "HARBOR PULSE  /  Synthetic data  /  Reproducible analysis figure - not a Power BI screenshot",
        fontsize=9,
        color="#526879",
    )
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / (name + ".png"))
    plt.close(fig)


fig, ax = figure("Operations: delay varies by terminal and month")
for k, name, color in [
    (1, "Zeebrugge", "#007F86"),
    (2, "Antwerpen", "#5064A0"),
    (3, "Gent", "#DA8956"),
]:
    values = []
    for m in range(1, 13):
        rows = [f for f in facts if f["TerminalKey"] == k and f["DateKey"] // 100 == 202600 + m]
        values.append(
            sum(f["Vehicles"] * f["DelayMinutes"] for f in rows) / sum(f["Vehicles"] for f in rows)
        )
    ax.plot(range(1, 13), values, "-o", label=name, color=color, lw=2)
ax.set_xlabel("Month / 2026")
ax.set_ylabel("Vehicle-weighted arrival delay / minutes")
ax.set_xticks(range(1, 13))
ax.legend(frameon=False)
ax.grid(alpha=0.15)
save(fig, "operations")
fig, ax = figure("Data quality: coverage is part of the KPI")
labels = ["Zeebrugge", "Antwerpen", "Gent"]
values = []
for k in (1, 2, 3):
    r = [f for f in facts if f["TerminalKey"] == k]
    values.append(100 * sum(f["CompleteDepartureUnits"] for f in r) / sum(f["Vehicles"] for f in r))
ax.barh(labels, values, color="#007F86")
ax.set_xlim(98.5, 100)
ax.axvline(99, color="#DA8956", ls="--", label="Publication minimum: 99%")
ax.set_xlabel("Valid departure coverage / %")
ax.legend(frameon=False)
for i, v in enumerate(values):
    ax.text(v - 0.04, i, f"{v:.2f}%", ha="right", va="center", color="white", fontweight="bold")
save(fig, "quality")
fig, ax = figure("Investment: compare uncertainty and ongoing costs")
for i, o in enumerate(decision["options"]):
    ax.errorbar(
        o["NettoP50"] / 1000,
        i,
        xerr=[[(o["NettoP50"] - o["NettoP10"]) / 1000], [(o["NettoP90"] - o["NettoP50"]) / 1000]],
        fmt="o",
        capsize=8,
        lw=3,
        color="#007F86" if i == 0 else "#5064A0",
    )
ax.set_yticks(range(3), ["Dispatch / slots", "Yard expansion", "Additional staffing"])
ax.invert_yaxis()
ax.axvline(0, color="#AAB9C5", ls="--")
ax.set_xlabel("Annual net value / EUR thousands; P10, P50, P90 of invented assumptions")
save(fig, "decision")
fig, ax = figure("Pilot: simulated result, not achieved business impact")
means = {(r["Groep"], r["Periode"]): r["GemiddeldeVertraging"] for r in pilot["summary"]}
for g, label, c in [("Interventie", "Intervention", "#007F86"), ("Controle", "Control", "#5064A0")]:
    ax.plot([0, 1], [means[g, "Voor"], means[g, "Na"]], "-o", label=label, color=c, lw=3)
ax.set_xticks([0, 1], ["Before", "After"])
ax.set_ylabel("Mean delay / minutes")
ax.legend(frameon=False)
ax.set_title("Observed DiD -7.06 min; generated effect -6 min; paired-day bootstrap", fontsize=11)
save(fig, "pilot")
fig, ax = figure("Regression: inspect what the model leaves unexplained")
for k, c in [(1, "#007F86"), (2, "#5064A0"), (3, "#DA8956")]:
    r = [r for r in diag["residual_plot"] if r["terminal"] == k]
    ax.scatter(
        [r["fitted"] for r in r],
        [r["residual"] for r in r],
        s=8,
        alpha=0.45,
        color=c,
        label=labels[k - 1],
    )
ax.axhline(0, color="#AAB9C5", ls="--")
ax.set_xlabel("Fitted delay / minutes")
ax.set_ylabel("Residual / minutes")
ax.legend(frameon=False)
save(fig, "diagnostics")
fig, ax = figure("Sensitivity: savings must be usable to matter")
for j, (label, c) in enumerate(
    [
        ("Dispatch / slots", "#007F86"),
        ("Yard expansion", "#5064A0"),
        ("Additional staffing", "#DA8956"),
    ]
):
    rows = [r for r in sens["grid"] if r["hour_value"] == 45]
    ax.plot(
        [r["fraction"] * 100 for r in rows],
        [r["options"][j]["annual_net"] / 1000 for r in rows],
        "-o",
        label=label,
        color=c,
    )
ax.axhline(0, color="#AAB9C5", ls="--")
ax.set_xlabel("Realizable fraction of saved waiting time / %")
ax.set_ylabel("Annual net value / EUR thousands")
ax.legend(frameon=False)
save(fig, "sensitivity")
fig, ax = figure("Pilot planning: detect meaningful effects, test the null")
for effect, c in [(0, "#AAB9C5"), (1.5, "#DA8956"), (3, "#007F86")]:
    rows = [r for r in planning["planning"] if r["effect_minutes"] == effect]
    ax.plot(
        [r["post_days"] for r in rows],
        [r["rejection_rate"] * 100 for r in rows],
        "-o",
        label=f"{effect:g} minute effect",
        color=c,
    )
ax.axhline(80, ls="--", color="#5064A0", label="Planning target: 80%")
ax.set_xlabel("Post-period independent days / baseline fixed at 14")
ax.set_ylabel("Simulated rejection rate / %")
ax.legend(frameon=False)
save(fig, "pilot-planning")
# PDF, exactly one A4 page; restrained typography and generous margins.
pdf = ROOT / "output/pdf/harbor-pulse-recruiter-brief.pdf"
pdf.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(pdf), pagesize=(595.28, 841.89))
c.setTitle("Harbor Pulse - Recruiter Brief")
c.setAuthor("Philippe Godfroy")
claim = json.loads((ROOT / "contracts/case-release.json").read_text())
c.setSubject(json.dumps(claim, separators=(",", ":")))
c.setFillColor(HexColor("#102A43"))
c.rect(0, 675, 596, 167, fill=1, stroke=0)
c.setFillColor(HexColor("#FFFFFF"))
c.setFont("Helvetica-Bold", 32)
c.drawString(42, 781, "Harbor Pulse")
c.setFont("Helvetica", 13)
c.drawString(43, 751, "From messy terminal events to defensible decisions")
c.setFont("Helvetica", 10)
c.drawString(43, 724, "Philippe Godfroy  |  AI-assisted synthetic portfolio case")
c.setFillColor(HexColor("#102A43"))


def line(y, text, size=10, bold=False):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(43, y, text)


line(644, "THE BUSINESS QUESTION", 10, True)
line(624, "How can terminals reduce delay without overstating savings or losing trust in data?")
line(591, "WHAT THE CASE BUILDS", 10, True)
for y, t in [
    (571, "Python + SQLite: versioned ingestion, quarantine, reconciliation and replay."),
    (554, "Power BI + weighted DAX: daily operations, quality, scenarios and decision support."),
    (537, "Investment comparison and pilot design: explicit costs, uncertainty and guardrails."),
]:
    line(y, t)
c.drawImage(
    str(OUT / "decision.png"), 78, 278, width=439, height=247, preserveAspectRatio=True, mask="auto"
)
line(249, "RECOMMENDATION: PILOT DISPATCH FIRST", 10, True)
line(230, "Under invented assumptions. No realized savings or real intervention effect is claimed.")
line(198, "EVIDENCE THAT CAN BE REVIEWED", 10, True)
line(
    179,
    "366,910 vehicle units  |  36 late revisions  |  216 duplicates skipped  |  0 reconciliation gap",
)
line(161, "Executable tests, CI, SQL/DAX examples, sensitivity, diagnostics and recovery evidence.")
line(128, "SCOPE AND LIMITS", 10, True)
line(109, "All source records and outcomes are fictitious. Native terminal roles are deployed.")
line(92, "Power BI screenshots/pixel review are online. RLS viewer tests remain license-blocked.")
line(76, "HP-2026.2 | 13 model tables | 56 measures | 12 pages | 132 report elements", 9)
line(57, "Case, walkthrough, code and evidence: github.com/phlppgdfry/harbor-pulse", 10, True)
c.linkURL("https://github.com/phlppgdfry/harbor-pulse", (40, 49, 551, 71), relative=0)
c.showPage()
c.save()
# Slides for a 120-second walkthrough: titles, 3 concise lines, actual figures.
slides = ROOT / "build/video"
slides.mkdir(exist_ok=True)
items = [
    (
        "The decision",
        "operations",
        [
            "Reduce waiting without moving queues.",
            "Three fictional terminals; a full synthetic year.",
            "Separate service, cost and data reliability.",
        ],
    ),
    (
        "Trust the denominator",
        "quality",
        [
            "216 duplicates skipped; 36 late revisions.",
            "Quarantine retains invalid and conflicting records.",
            "Missing departure coverage stays visible.",
        ],
    ),
    (
        "Compare investments",
        "decision",
        [
            "Subtract recurring cost; disclose one-off investment.",
            "Count only usable waiting-time savings.",
            "Pilot dispatch first under the stated assumptions.",
        ],
    ),
    (
        "Stress-test the recommendation",
        "sensitivity",
        [
            "Low realizable value can erase the business case.",
            "Sensitivity includes zero benefit and first-year cash.",
            "Regression associations are not intervention effects.",
        ],
    ),
    (
        "Test an intervention",
        "pilot",
        [
            "Day-blocked lane assignment and paired-day inference.",
            "Observed result is simulated, not achieved impact.",
            "Plan for smaller effects, dropout and spillover.",
        ],
    ),
    (
        "Inspect and reproduce",
        "diagnostics",
        [
            "Read the SQL, DAX, tests and recovery evidence.",
            "No Microsoft account needed to run the core case.",
            "AI-assisted portfolio work by Philippe Godfroy.",
        ],
    ),
]
for i, (title, image, lines) in enumerate(items):
    fig = plt.figure(figsize=(16, 9), dpi=120)
    fig.text(0.055, 0.91, title, fontsize=28, fontweight="bold")
    ax = fig.add_axes([0.05, 0.20, 0.64, 0.63])
    ax.imshow(plt.imread(OUT / (image + ".png")))
    ax.axis("off")
    for j, line in enumerate(lines):
        import textwrap

        fig.text(
            0.72,
            0.68 - j * 0.15,
            "\n".join(textwrap.wrap(line, 29)),
            fontsize=14,
            color="#243B53",
            va="top",
        )
    fig.text(
        0.055,
        0.085,
        "HARBOR PULSE  /  Synthetic evidence walkthrough  /  Analysis figures, not Power BI screenshots",
        fontsize=11,
    )
    fig.savefig(slides / f"slide-{i}.png")
    plt.close(fig)
print("Generated 7 evidence figures, one-page PDF and 6 video slides")
