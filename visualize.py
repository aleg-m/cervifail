"""
cervifail/visualize.py
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BG       = "#0D1117"
PANEL_BG = "#161B22"
GRID     = "#21262D"
TEXT_HI  = "#E6EDF3"
TEXT_LO  = "#8B949E"
CRITICAL = "#FF4560"
ELEVATED = "#FF8C42"
MODERATE = "#FFD166"
LOW_C    = "#06D6A0"
ACCENT   = "#58A6FF"

TIER_COLOR = {"Critical": CRITICAL, "Elevated": ELEVATED, "Moderate": MODERATE, "Low": LOW_C}

AXIS_STYLE = dict(
    gridcolor=GRID, linecolor="#30363D",
    tickfont=dict(color=TEXT_LO, size=10),
    title_font=dict(color=TEXT_LO, size=11),
    zerolinecolor=GRID,
)

def build_dashboard(patients, outputs, html_path="cervifail_dashboard.html"):
    n = len(outputs)
    tiers  = [o.risk_tier for o in outputs]
    gas    = [o.gestational_age_decimal for o in outputs]
    cls_   = [o.cl_used_cm for o in outputs]
    probs  = [o.p_cervical_insufficiency for o in outputs]
    csiss  = [o.csis for o in outputs]
    pids   = [p.patient_id for p in patients]
    colors = [TIER_COLOR[t] for t in tiers]
    tc     = {t: tiers.count(t) for t in ["Critical","Elevated","Moderate","Low"]}
    high   = tc["Critical"] + tc["Elevated"]

    fig = make_subplots(
        rows=3, cols=2,
        specs=[[{"type":"domain"},{"type":"xy"}],[{"type":"xy"},{"type":"xy"}],
               [{"colspan":2,"type":"table"},None]],
        subplot_titles=["Risk Tier Distribution",
                        "P(CI) by Gestational Age",
                        "Cervical Length Distribution",
                        "CSIS vs P(Cervical Insufficiency)",
                        "Patient Risk Register — All Patients (ranked by P(CI))"],
        vertical_spacing=0.10, horizontal_spacing=0.08,
        row_heights=[0.30, 0.33, 0.30],
    )

    # 1. Donut
    fig.add_trace(go.Pie(
        labels=["Critical","Elevated","Moderate","Low"],
        values=[tc[t] for t in ["Critical","Elevated","Moderate","Low"]],
        marker_colors=[CRITICAL,ELEVATED,MODERATE,LOW_C],
        hole=0.60, textinfo="label+value",
        textfont=dict(color=TEXT_HI, size=11),
        hovertemplate="<b>%{label}</b><br>n=%{value}  (%{percent})<extra></extra>",
        showlegend=False,
    ), row=1, col=1)
    fig.add_annotation(x=0.20, y=0.78,
        text=f"<b>{high/n*100:.0f}%</b><br><span style='font-size:10px;color:{TEXT_LO}'>HIGH RISK</span>",
        font=dict(color=CRITICAL if high/n>=0.4 else ELEVATED, size=20),
        showarrow=False, align="center", xref="paper", yref="paper")

    # 2. P(CI) by GA
    fig.add_trace(go.Scatter(
        x=gas, y=probs, mode="markers",
        marker=dict(color=colors, size=11, line=dict(color=BG, width=1)),
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        customdata=[f"{pids[i]} | GA:{gas[i]:.1f}w | CL:{cls_[i]:.2f}cm | P(CI):{probs[i]*100:.1f}% | {tiers[i]}" for i in range(n)],
        name="",
    ), row=1, col=2)
    fig.add_trace(go.Scatter(  # threshold line
        x=[min(gas)-0.2, max(gas)+0.2], y=[0.5, 0.5],
        mode="lines", line=dict(color=CRITICAL, width=1, dash="dash"),
        opacity=0.7, hoverinfo="skip", showlegend=False, name="",
    ), row=1, col=2)
    fig.update_xaxes(title_text="Gestational Age (weeks)", row=1, col=2, **AXIS_STYLE)
    fig.update_yaxes(title_text="P(Cervical Insufficiency)", tickformat=".0%", range=[0,1], row=1, col=2, **AXIS_STYLE)

    # 3. Histogram
    fig.add_trace(go.Histogram(
        x=cls_, nbinsx=12, marker_color=ACCENT,
        marker_line_color=BG, marker_line_width=1.5, opacity=0.85,
        hovertemplate="CL: %{x:.2f} cm | n=%{y}<extra></extra>", name="",
    ), row=2, col=1)
    mean_cl = sum(cls_) / n
    for xv, clr, lbl in [(mean_cl, ELEVATED, f"Mean {mean_cl:.2f}cm"), (2.5, CRITICAL, "2.5cm")]:
        fig.add_trace(go.Scatter(
            x=[xv, xv], y=[0, n+1], mode="lines",
            line=dict(color=clr, width=1.5, dash="dash"),
            hoverinfo="skip", showlegend=False, name=lbl,
        ), row=2, col=1)
    fig.update_xaxes(title_text="Cervical Length (cm)", row=2, col=1, **AXIS_STYLE)
    fig.update_yaxes(title_text="Patients (n)", row=2, col=1, **AXIS_STYLE)

    # 4. CSIS vs P(CI)
    fig.add_trace(go.Scatter(
        x=csiss, y=probs, mode="markers",
        marker=dict(color=colors, size=[max(8, c*6) for c in cls_],
                    line=dict(color=BG, width=1), sizemode="diameter"),
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        customdata=[f"{pids[i]} | CSIS:{csiss[i]:.2f} | P(CI):{probs[i]*100:.1f}% | {tiers[i]}" for i in range(n)],
        name="",
    ), row=2, col=2)
    cr = np.linspace(min(csiss)-0.5, max(csiss)+0.5, 300)
    fig.add_trace(go.Scatter(
        x=cr, y=1/(1+np.exp(1.2*(cr-8.0))),
        mode="lines", line=dict(color=ACCENT, width=1.5, dash="dot"),
        opacity=0.5, hoverinfo="skip", name="Sigmoid",
    ), row=2, col=2)
    fig.add_trace(go.Scatter(
        x=[min(csiss)-0.3, max(csiss)+0.3], y=[0.5, 0.5],
        mode="lines", line=dict(color=CRITICAL, width=1, dash="dash"),
        opacity=0.7, hoverinfo="skip", showlegend=False, name="",
    ), row=2, col=2)
    fig.update_xaxes(title_text="CSIS (Cervical Structural Integrity Score)", row=2, col=2, **AXIS_STYLE)
    fig.update_yaxes(title_text="P(Cervical Insufficiency)", tickformat=".0%", range=[0,1], row=2, col=2, **AXIS_STYLE)

    # 5. Table
    si = sorted(range(n), key=lambda i: probs[i], reverse=True)
    row_bg = ["#1f1014" if tiers[i] in ("Critical","Elevated") else PANEL_BG for i in si]
    fig.add_trace(go.Table(
        header=dict(
            values=["<b>Patient</b>","<b>GA</b>","<b>CL (MATLAB)</b>",
                    "<b>Eq.A Predicted CL</b>","<b>CSIS</b>","<b>P(CI)</b>","<b>Risk Tier</b>"],
            fill_color="#21262D", font=dict(color=TEXT_HI, size=11),
            line_color=GRID, align="center", height=34,
        ),
        cells=dict(
            values=[
                [pids[i] for i in si],
                [f"{gas[i]:.1f}w" for i in si],
                [f"{cls_[i]:.3f} cm" for i in si],
                [f"{outputs[i].cl_predicted_cm:.3f} cm" for i in si],
                [f"{csiss[i]:.2f}" for i in si],
                [f"{probs[i]*100:.1f}%" for i in si],
                [tiers[i] for i in si],
            ],
            fill_color=[row_bg]*6 + [[TIER_COLOR[tiers[i]] for i in si]],
            font=dict(color=[*[[TEXT_HI]*n]*6, [BG]*n], size=11),
            line_color=GRID, align="center", height=28,
        ),
    ), row=3, col=1)

    fig.update_layout(
        title=dict(
            text="<b>CERVIFAIL</b>  <span style='font-size:13px;color:#8B949E'>Cervical Failure Risk · Clinical Decision Support · Cohort Dashboard</span>",
            font=dict(color=TEXT_HI, size=22), x=0.02, y=0.99,
        ),
        paper_bgcolor=BG, plot_bgcolor=PANEL_BG,
        font=dict(family="'IBM Plex Mono', monospace", color=TEXT_HI),
        margin=dict(l=40, r=40, t=80, b=30),
        height=1080, showlegend=False,
        hoverlabel=dict(bgcolor=PANEL_BG, bordercolor=GRID, font=dict(color=TEXT_HI, size=11)),
    )
    for ann in fig.layout.annotations:
        ann.font.color = TEXT_LO
        ann.font.size  = 11

    fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)
    print(f"  Dashboard (HTML) → {html_path}")
    return html_path