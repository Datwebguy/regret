"""Build the Alpaca OAuth DDQ response and a factual security-practices PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(r"C:\Users\DELL\Downloads\REGRET-alpaca-uploads")
INK = colors.HexColor("#1a1612")
RULE = colors.HexColor("#9e9176")
HEAD = colors.HexColor("#241e18")
SHEET = colors.HexColor("#f4eee0")
WARN = colors.HexColor("#f3e2c4")


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "t", parent=base["Title"], fontName="Times-Bold", fontSize=18,
            leading=22, textColor=INK, alignment=TA_LEFT, spaceAfter=8,
        ),
        "h": ParagraphStyle(
            "h", parent=base["Heading2"], fontName="Times-Bold", fontSize=13,
            leading=16, textColor=INK, spaceBefore=14, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "b", parent=base["BodyText"], fontName="Times-Roman", fontSize=10,
            leading=13, textColor=INK, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "s", parent=base["BodyText"], fontName="Times-Roman", fontSize=8.5,
            leading=11, textColor=INK, spaceAfter=4,
        ),
        "cell": ParagraphStyle(
            "c", parent=base["BodyText"], fontName="Times-Roman", fontSize=9,
            leading=12, textColor=INK,
        ),
        "you": ParagraphStyle(
            "y", parent=base["BodyText"], fontName="Times-Bold", fontSize=9,
            leading=12, textColor=colors.HexColor("#8e2a24"),
        ),
    }


def row(label: str, value: str, s, you: bool = False) -> list:
    return [
        Paragraph(f"<b>{label}</b>", s["cell"]),
        Paragraph(value, s["you"] if you else s["cell"]),
    ]


def table(rows, col1=2.3 * inch, col2=4.4 * inch):
    t = Table(rows, colWidths=[col1, col2], repeatRows=0)
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (0, -1), SHEET),
            ]
        )
    )
    return t


def build_ddq() -> Path:
    s = styles()
    path = OUT / "REGRET-OAuth-DDQ-V3-responses.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="REGRET OAuth Due Diligence Questionnaire responses",
    )
    story = [
        Paragraph("OAuth Due Diligence Questionnaire — REGRET responses", s["title"]),
        Paragraph(
            "Prepared for AlpacaDB, Inc. / Alpaca Securities LLC review. "
            "This document answers OAuth DDQ v.3 (03.26) for the REGRET application. "
            "It is a factual description of the product as deployed at "
            "https://regret.fly.dev. It is not legal advice and does not claim "
            "that REGRET is a registered broker-dealer or investment adviser.",
            s["body"],
        ),
        Paragraph(
            "Operator identity as provided by the applicant: Isheno Ebenezer. "
            "No separate legal entity has been formed for REGRET. "
            "Contact email used for this application: princeabel2000@gmail.com.",
            s["body"],
        ),
        Paragraph("Company structure and ownership", s["h"]),
        table(
            [
                row("Full Legal Company Name", "Isheno Ebenezer (sole operator of the REGRET application)", s),
                row("Company Type (Inc, LLC, Ltd)", "Sole proprietorship / unincorporated. No Inc, LLC, or Ltd has been formed.", s),
                row(
                    "State or Country of Incorporation",
                    "Not incorporated. REGRET is operated as a sole proprietorship by Isheno Ebenezer.",
                    s,
                ),
                row("Beneficial Owners &gt;25%", "Isheno Ebenezer — 100%", s),
                row(
                    "Authorized Persons (names and titles) in contact with Alpaca",
                    "Isheno Ebenezer, Operator · princeabel2000@gmail.com",
                    s,
                ),
                row("Company Website", "https://regret.fly.dev", s),
                row(
                    "Type of Entity (registered, regulated, licensed)",
                    "Unregistered technology application. Not a registered broker-dealer. "
                    "Not a registered investment adviser. No other financial licenses are held.",
                    s,
                ),
                row(
                    "Organizational chart",
                    "Isheno Ebenezer (Operator, 100%) → REGRET application at https://regret.fly.dev. "
                    "There are no employees, subsidiaries, or other owners.",
                    s,
                ),
            ]
        ),
        Paragraph("Agreements", s["h"]),
        table(
            [
                row(
                    "End User Agreements / Terms and Conditions",
                    "https://regret.fly.dev/terms (public HTML). A PDF print of the same page can be attached.",
                    s,
                ),
                row(
                    "Fee / Pricing Schedules or Agreements",
                    "None. REGRET does not currently charge users a fee. No pricing schedule exists. "
                    "If pricing is introduced, an updated schedule will be provided.",
                    s,
                ),
                row(
                    "Privacy Policy",
                    "https://regret.fly.dev/privacy (public HTML). A PDF print of the same page can be attached.",
                    s,
                ),
                row(
                    "Cybersecurity Policy",
                    "See attached “REGRET Information Security Practices” "
                    "(REGRET-information-security-practices.pdf). That document describes current "
                    "engineering controls. It is not a certified ISO/SOC policy.",
                    s,
                ),
            ]
        ),
        Paragraph("Business description", s["h"]),
        table(
            [
                row(
                    "Business model, products, technology, and services",
                    "REGRET is a trading decision application. A user creates a REGRET login "
                    "(separate from any brokerage account), writes rules, and submits a trade idea. "
                    "REGRET evaluates the idea against market data it can retrieve, the user’s rules, "
                    "and — only if the user connects a brokerage — that user’s real account. "
                    "It returns a structured verdict (buy, wait, reduce, reject, or incomplete). "
                    "It does not invent prices, balances, orders, or fills. "
                    "It never sends an order unless the user reviews a preview and explicitly confirms. "
                    "Connecting a brokerage is optional. The supported method is Alpaca Connect (OAuth 2.0) "
                    "with scopes data and trading. REGRET does not request account:write. "
                    "Paper and live are separate. The current public deployment has live order submission disabled. "
                    "REGRET is not a broker-dealer, does not open or custody brokerage accounts, "
                    "and does not manage money. Brokerage services, when used, are provided by Alpaca. "
                    "REGRET is not copy trading, mirror trading, or an influencer-signal product. "
                    "It does not automatically copy another person’s trades into a user’s account.",
                    s,
                ),
                row(
                    "Do you currently have customers? How many?",
                    "Pre-launch. No paying customers. Operator and internal testing only.",
                    s,
                ),
                row(
                    "How do you protect network endpoints and workstations against malicious code?",
                    "Production runs as a single Fly.io machine (HTTPS, force_https). "
                    "The operator workstation uses current OS updates and standard endpoint protection. "
                    "Application dependencies are installed from package indexes at image build. "
                    "There is no corporate office network. See the attached security-practices PDF.",
                    s,
                ),
                row(
                    "Video or screenshots of Alpaca connect",
                    "Will be attached to the email: a screen recording (not Loom) of "
                    "REGRET → Settings → Broker → required disclosure with Deny/Allow → Connect. "
                    "OAuth authorize currently returns unknown client until this review is complete.",
                    s,
                ),
            ]
        ),
        Paragraph("Process acknowledgement (DDQ page 3)", s["h"]),
        Paragraph(
            "The live Settings → Broker page shows the required disclosure before OAuth starts:",
            s["body"],
        ),
        Paragraph("<b>Authorize REGRET</b>", s["body"]),
        Paragraph(
            "By allowing REGRET to access your Alpaca account, you are granting REGRET access "
            "to your account information and authorization to place transactions at your direction.",
            s["body"],
        ),
        Paragraph(
            "Alpaca does not warrant or guarantee that REGRET will work as advertised or expected. "
            "Before authorizing, learn more about REGRET.",
            s["body"],
        ),
        Paragraph(
            "The user must choose <b>Deny</b> (no redirect) or <b>Allow</b> (then REGRET starts the official "
            "Alpaca OAuth authorize URL). Acknowledgement happens before the Alpaca redirect.",
            s["body"],
        ),
        Paragraph("Do’s and don’ts (positioning)", s["h"]),
        Paragraph(
            "REGRET is positioned as an application / decision tool. It is not described as a "
            "broker-dealer, licensed trader, or investment adviser. Marketing and in-product copy "
            "state that REGRET does not open brokerage accounts and that brokerage services are "
            "provided by Alpaca. Verdicts are structured checks, not personalized investment advice. "
            "Alpaca’s name is used only to describe the optional brokerage connection, not as a "
            "co-brand or endorsement.",
            s["body"],
        ),
        Spacer(1, 10),
        Paragraph(
            "App: REGRET · Website: https://regret.fly.dev · "
            "Redirect: https://regret.fly.dev/api/alpaca/callback · "
            "Requested scopes: data, trading · Live trading on this deployment: disabled.",
            s["small"],
        ),
    ]
    doc.build(story)
    return path


def build_security() -> Path:
    s = styles()
    path = OUT / "REGRET-information-security-practices.pdf"
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="REGRET Information Security Practices",
    )
    bullets = [
        "REGRET account identifiers and email.",
        "Password hashes (bcrypt). Passwords are not stored in recoverable form.",
        "Session tokens, hashed (SHA-256) at rest. Browser sessions use an HttpOnly, Secure, SameSite=Lax cookie.",
        "User-created rules, analyses, journal entries, and order records.",
        "Alpaca OAuth tokens or user-supplied API keys, encrypted at rest (Fernet) and never returned to the browser.",
        "Short-lived OAuth state. Application audit events (no passwords or raw tokens).",
    ]
    story = [
        Paragraph("REGRET Information Security Practices", s["title"]),
        Paragraph("Effective 13 August 2026. Describes current controls on https://regret.fly.dev.", s["small"]),
        Paragraph(
            "This is a description of how the application is built and hosted today. "
            "It is not an ISO 27001, SOC 2, or other certified information-security program. "
            "No internet service is free of risk.",
            s["body"],
        ),
        Paragraph("Data classification and handling", s["h"]),
        Paragraph(
            "REGRET data is treated as confidential user data. Classes in use:",
            s["body"],
        ),
        ListFlowable(
            [ListItem(Paragraph(b, s["body"])) for b in bullets],
            bulletType="bullet",
            leftIndent=14,
        ),
        Paragraph(
            "Personal data is not sold. One user’s records are isolated from another’s. "
            "Missing market or account data is shown as missing and is not replaced with zero or invented figures.",
            s["body"],
        ),
        Paragraph("Access control and privileged access", s["h"]),
        Paragraph(
            "End users access only their own REGRET account after authentication. "
            "Browser login does not return a raw session token. CLI/MCP may use a bearer token the user stores. "
            "Login and registration are rate-limited. Failed attempts do not reveal whether an email exists. "
            "Production secrets (application keys, Alpaca OAuth client secret, encryption key) are stored as "
            "Fly.io secrets, not in the git repository. There is a single production machine and a single operator.",
            s["body"],
        ),
        Paragraph("Encryption in transit and at rest", s["h"]),
        Paragraph(
            "The public site is HTTPS only (Fly force_https). Alpaca OAuth and API calls use HTTPS. "
            "Alpaca credentials are encrypted at rest before they are written to the application database. "
            "Passwords are hashed with bcrypt (cost 12). Session identifiers are hashed with SHA-256.",
            s["body"],
        ),
        Paragraph("Vulnerability and patch management", s["h"]),
        Paragraph(
            "The production image is rebuilt from current Python and Node base images when the application is deployed. "
            "Application dependencies are pinned via the project lockfiles at build time. "
            "There is no formal scheduled penetration-test program at this stage.",
            s["body"],
        ),
        Paragraph("Incident response and disaster recovery", s["h"]),
        Paragraph(
            "The operator is the incident contact. If credentials are believed exposed, the operator revokes "
            "sessions, rotates Fly secrets, and users can disconnect brokerage in Settings (stored Alpaca "
            "tokens for that environment are removed). The application database lives on a Fly volume. "
            "There is not yet a documented multi-region failover. Rate-limit counters are in-memory and reset on restart.",
            s["body"],
        ),
        Paragraph("Physical security", s["h"]),
        Paragraph(
            "REGRET has no company office that stores customer systems. Compute and disk are in Fly.io’s "
            "Ashburn (iad) region. Physical security of that facility is Fly.io’s responsibility. "
            "The operator’s workstation is a personal computer with OS updates.",
            s["body"],
        ),
        Paragraph("Vendor risk management", s["h"]),
        Paragraph(
            "Material vendors: Fly.io (hosting and data volume); Alpaca (brokerage OAuth, market data, and "
            "order routing when a user connects); Google Fonts (typefaces on public pages). "
            "Users who connect a brokerage are also subject to Alpaca’s own agreements and privacy policy. "
            "No advertising networks are used.",
            s["body"],
        ),
        Paragraph("Contact", s["h"]),
        Paragraph(
            "Security contact: Isheno Ebenezer, Operator · princeabel2000@gmail.com. "
            "Service: https://regret.fly.dev",
            s["body"],
        ),
    ]
    doc.build(story)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ddq = build_ddq()
    sec = build_security()
    print(ddq)
    print(sec)


if __name__ == "__main__":
    main()
