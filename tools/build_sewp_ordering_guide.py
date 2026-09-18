#!/usr/bin/env python3
"""Generate the Vidoori NASA SEWP VI electronic ordering guide as a PDF.

    python3 tools/build_sewp_ordering_guide.py
    python3 tools/build_sewp_ordering_guide.py --check

Writes assets/docs/Vidoori_SEWP_VI_Ordering_Guide.pdf using tools/pdfkit.py.
Python 3 standard library only.

WHY THIS EXISTS

The SEWP contract requires an electronic ordering guide, published so SEWP
customers can download and print it, available before the first delivery order
and re-issued within ten business days of every contract modification. The
required contents come from the CHUM:

  1. How to obtain a quote for hardware, software, or services, including the
     names, telephone numbers and email addresses of the appropriate sales
     representatives.
  2. Policy and procedural information covering installation, basic warranty,
     extended warranty, technical support, software support and other
     post-delivery issues, with named support staff and their contacts.
  3. How to troubleshoot a problematic order, with named contacts.
  4. Overview information about Vidoori and the SEWP contracts.

Each of those is a numbered section below, so an auditor can map the document
to the clause without interpretation.

ACCESSIBILITY

The guide is generated tagged: a real structure tree, headings marked /H1 and
/H2, body text /P, the badge a /Figure with /Alt, decoration marked
/Artifact, plus /Lang and /DisplayDocTitle. That is built to PDF/UA-1, which
is what Section 508 maps to for documents.

Generating to the standard is not the same as passing an audit. Validate:

    verapdf -f ua1 --format text assets/docs/Vidoori_SEWP_VI_Ordering_Guide.pdf

DRAFT STATUS

Every value the program manager has not supplied is written as [TBD: ...] and
listed by --check. The cover carries a DRAFT banner while any remain. Do not
issue to SEWP until --check reports none.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdfkit  # noqa: E402

# ---------------------------------------------------------------------------
# Content. Edit this, not the layout code.
# ---------------------------------------------------------------------------

VERSION = "[TBD: version]"
EFFECTIVE = "[TBD: effective date]"
CONTRACT_NUMBER = "80TECH26D1457"

CONTACTS = {
    "quotes": {
        "role": "Quotes and sales",
        "name": "[TBD: name]",
        "title": "[TBD: title]",
        "phone": "[TBD: direct telephone]",
        "email": "[TBD: direct email]",
    },
    "support": {
        "role": "Post-delivery support",
        "name": "[TBD: name]",
        "title": "[TBD: title]",
        "phone": "[TBD: direct telephone]",
        "email": "[TBD: direct email]",
    },
    "orders": {
        "role": "Order troubleshooting",
        "name": "[TBD: name]",
        "title": "[TBD: title]",
        "phone": "[TBD: direct telephone]",
        "email": "[TBD: direct email]",
    },
    "pm": {
        "role": "Program Manager",
        "name": "Gregory Gilleland",
        "title": "SEWP VI Program Manager",
        "phone": "[TBD: direct telephone]",
        "email": "[TBD: direct email]",
    },
    "dpm": {
        "role": "Deputy Program Manager",
        "name": "Haley Kubal",
        "title": "SEWP VI Deputy Program Manager",
        "phone": "[TBD: direct telephone]",
        "email": "[TBD: direct email]",
    },
}

CONTRACT_FACTS = [
    ("Contract number", CONTRACT_NUMBER),
    ("Vehicle", "NASA SEWP VI Government-Wide Acquisition Contract"),
    ("Category", "C - ITC/AV Mission-Based Services"),
    ("Award date", "July 2, 2026"),
    ("Effective date", "[TBD: pending contract modification]"),
    ("Ordering period", "Ten years from the effective date"),
    ("Contract holder", "Vidoori, Inc."),
    ("UEI", "N37JST95C3S5"),
    ("CAGE code", "6T0A7"),
    ("Primary NAICS", "541512 - Computer Systems Design Services"),
    ("Business size", "Small Business"),
]

SECTIONS = [
    {
        "n": "1",
        "title": "About Vidoori and the SEWP VI contract",
        "chum": "Overview information about the contractor and the SEWP contracts.",
        "blocks": [
            ("p", "Vidoori, Inc. is a consulting firm providing high quality information "
                  "technology services and products that solve real business problems for "
                  "Government and Commercial clients. Vidoori was founded in 2008 and is "
                  "headquartered at 4000 Garden City Drive, Suite 808, Hyattsville, Maryland "
                  "20785."),
            ("p", "Vidoori is appraised at CMMI V3.0 Maturity Level 3 for both Development and "
                  "Services, is certified to ISO 9001:2015 and ISO/IEC 20000-1:2018, and "
                  "maintains a DCAA-compliant accounting system."),
            ("h3", "The SEWP VI contract"),
            ("p", "Solutions for Enterprise-Wide Procurement (SEWP) VI is a multiple-award "
                  "Government-Wide Acquisition Contract managed by the NASA SEWP Program "
                  "Office. It provides NASA and all U.S. federal agencies a route to "
                  "information technology, communications, and audio/visual products, "
                  "solutions and services."),
            ("p", "Vidoori holds Category C, ITC/AV Mission-Based Services. Because SEWP VI is "
                  "a multiple-award contract, ordering agencies provide all eligible Category C "
                  "contract holders a fair opportunity to be considered for each order in "
                  "accordance with FAR 16.505(b), except as provided by law."),
            ("facts", None),
            ("h3", "Delivery areas"),
            ("p", "Vidoori supports mission-based ITC/AV services requirements across "
                  "integration and test, cloud-native engineering, DevSecOps, and data "
                  "management. Ancillary products may support a mission-based services "
                  "requirement."),
        ],
    },
    {
        "n": "2",
        "title": "How to obtain a quote",
        "chum": "How to obtain a quote for hardware, software or services, including the "
                "names, telephone numbers and email addresses of the appropriate sales "
                "representatives.",
        "blocks": [
            ("p", "Federal customers request quotes through the NASA SEWP Quote Request Tool "
                  "(QRT) at www.sewp.nasa.gov. Vidoori quotes only offerings that are on "
                  "contract in the SEWP database of record, at or below the contract price."),
            ("h3", "Submitting a request"),
            ("p", "1. Define the requirement. State the services sought, the performance work "
                  "statement or statement of work, the period of performance, the evaluation "
                  "criteria, and the response date."),
            ("p", "2. Submit through the QRT. Select Category C, the applicable NAICS code, "
                  "and the business size designation. The request routes to eligible contract "
                  "holders under FAR 16.505(b)."),
            ("p", "3. Receive and evaluate quotes. Vidoori responds within the timeframe stated "
                  "in the request. Evaluate responses against the criteria you stated and "
                  "document the selection according to your agency procedures."),
            ("p", "4. Place the order. Route the delivery order through the SEWP Program "
                  "Office, referencing the Vidoori contract number and the selected quote."),
            ("h3", "Sales representative"),
            ("contact", "quotes"),
            ("p", "Customers who prefer to discuss a requirement before issuing a request may "
                  "contact the representative above directly. Doing so does not replace the "
                  "QRT; the formal request must still be submitted through it."),
            ("h3", "Pricing and payment"),
            ("p", "Quoted prices are at or below the contract price for the offering. Vidoori "
                  "accepts the Government Purchase Card. The SEWP administrative charge is "
                  "embedded in offering prices by contract and is never quoted or invoiced as "
                  "a separate line item."),
        ],
    },
    {
        "n": "3",
        "title": "Post-delivery support",
        "chum": "Policy and procedural information on installation, basic warranty, extended "
                "warranty, technical support, software support and other post-delivery "
                "issues, with named support staff and their contacts.",
        "blocks": [
            ("h3", "Support contact"),
            ("contact", "support"),
            ("h3", "Installation"),
            ("p", "Where installation is within the scope of the delivery order, Vidoori "
                  "coordinates scheduling with the customer point of contact named on the "
                  "order before work begins. Site access, security clearance and government "
                  "furnished equipment requirements are confirmed in advance. Installation is "
                  "complete on customer acceptance, recorded in writing."),
            ("h3", "Basic warranty"),
            ("p", "Services are warranted to conform to the requirements of the delivery "
                  "order. Products supplied as ancillary to a services requirement carry the "
                  "manufacturer's standard warranty, passed through to the customer unchanged. "
                  "Report a warranty issue to the support contact above; Vidoori acknowledges "
                  "within one business day."),
            ("h3", "Extended warranty"),
            ("p", "Extended warranty or extended manufacturer support may be quoted as a line "
                  "item on the delivery order where the manufacturer offers it. Extended "
                  "coverage is not provided by default and must be requested at quote time."),
            ("h3", "Technical support"),
            ("p", "Technical support for services delivered under the contract is provided "
                  "during the hours stated in the delivery order. Where the order does not "
                  "state hours, support is available 0800 to 1700 Eastern Time, Monday to "
                  "Friday, excluding federal holidays. Contact the support representative "
                  "above."),
            ("h3", "Software support"),
            ("p", "Where software is supplied, support follows the publisher's terms, which "
                  "are provided with the quote. Vidoori acts as the customer's first point of "
                  "contact and coordinates with the publisher on the customer's behalf rather "
                  "than referring the customer onward."),
            ("h3", "Other post-delivery issues"),
            ("p", "Invoicing questions, delivery discrepancies, returns and replacements are "
                  "handled by the support contact above. Where an issue requires escalation, "
                  "it is escalated to the Program Manager named in section 5."),
        ],
    },
    {
        "n": "4",
        "title": "Troubleshooting a problematic order",
        "chum": "How to troubleshoot a problematic order, with named contacts.",
        "blocks": [
            ("h3", "Order support contact"),
            ("contact", "orders"),
            ("h3", "What to have ready"),
            ("p", "Provide the SEWP request or order number, the Vidoori contract number, the "
                  "quote number if one was issued, the delivery order number, and a short "
                  "description of the problem. Having these to hand lets Vidoori locate the "
                  "order without a further exchange."),
            ("h3", "How an issue is handled"),
            ("p", "1. Acknowledgement. Vidoori acknowledges a reported problem within one "
                  "business day and names the person who owns it."),
            ("p", "2. Investigation. Vidoori identifies the cause and tells the customer what "
                  "is required to resolve it, including anything needed from the agency."),
            ("p", "3. Resolution. Vidoori confirms resolution in writing to the customer point "
                  "of contact and, where the SEWP Program Office was involved, to the Program "
                  "Office."),
            ("h3", "Escalation"),
            ("p", "If an issue is not progressing, escalate to the Program Manager and then "
                  "the Deputy Program Manager, both named in section 5. Customers may also "
                  "raise an issue with the NASA SEWP Program Office at any point."),
        ],
    },
    {
        "n": "5",
        "title": "Program management contacts",
        "chum": "Program management contact information, maintained without email aliases.",
        "blocks": [
            ("p", "The contacts below are named individuals with direct telephone numbers and "
                  "direct email addresses. Vidoori maintains them with the SEWP Program "
                  "Management Office and reissues this guide when they change."),
            ("contact", "pm"),
            ("contact", "dpm"),
            ("h3", "Keeping this guide current"),
            ("p", "This guide is republished within ten business days of every contract "
                  "modification. The current version is always available at "
                  "vidoori.com/sewp."),
        ],
    },
]

# ---------------------------------------------------------------------------
# Brand tokens, matching assets/css/site.css.
# ---------------------------------------------------------------------------

NAVY_950 = (0.078, 0.082, 0.169)
NAVY_900 = (0.114, 0.118, 0.235)
NAVY_700 = (0.255, 0.263, 0.447)
NAVY_200 = (0.788, 0.796, 0.875)
NAVY_50 = (0.957, 0.957, 0.976)
GREEN_400 = (0.604, 0.827, 0.537)
GREEN_700 = (0.247, 0.478, 0.173)
GRAY_600 = (0.357, 0.376, 0.439)
WHITE = (1, 1, 1)

# Liberation Sans, embedded because PDF/UA requires the font program to be in
# the file. SIL Open Font Licensed, so both embedding and redistribution are
# permitted, and metric-compatible with Helvetica, so the layout is identical
# to the untagged base-14 output.
#
# The faces are committed under tools/fonts/ rather than read from the system.
# They are a build input like tools/sewp-badge-for-pdf.jpg: reading them from
# ~/Library/Fonts worked on the machine that had the Homebrew cask installed
# and broke CI immediately, because the runner is Ubuntu and has neither the
# path nor the font. tools/fonts/LICENSE is the OFL text, which the licence
# requires be distributed alongside.
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONTS = {
    "F1": os.path.join(FONT_DIR, "LiberationSans-Regular.ttf"),
    "F2": os.path.join(FONT_DIR, "LiberationSans-Bold.ttf"),
}

MARGIN = 58.0
PAGE_W, PAGE_H = 612.0, 792.0
TEXT_W = PAGE_W - 2 * MARGIN
BOTTOM = 76.0
TOP = PAGE_H - MARGIN


class Flow:
    """Lays content down the page and starts a new one when it runs out."""

    def __init__(self, doc, badge_name=None):
        self.doc = doc
        self.badge = badge_name
        self.page = None
        self.y = 0.0
        self.n = 0

    def new_page(self):
        self.n += 1
        self.page = self.doc.page(PAGE_W, PAGE_H)
        p = self.page
        # Running head and foot are decoration, not content.
        p.artifact(lambda: (
            p.line(MARGIN, TOP + 14, PAGE_W - MARGIN, TOP + 14, NAVY_200, 0.6),
            p.text(MARGIN, TOP + 20, "Vidoori NASA SEWP VI Ordering Guide", 7.5, GRAY_600),
            p.text(MARGIN, TOP + 20, "Page %d" % self.n, 7.5, GRAY_600,
                   align="right", maxw=TEXT_W),
            p.line(MARGIN, BOTTOM - 16, PAGE_W - MARGIN, BOTTOM - 16, NAVY_200, 0.6),
            p.text(MARGIN, BOTTOM - 28, VERSION + "  |  Effective " + EFFECTIVE, 7, GRAY_600),
            p.text(MARGIN, BOTTOM - 28, "vidoori.com/sewp", 7, GRAY_600,
                   align="right", maxw=TEXT_W),
        ))
        self.y = TOP

    def need(self, h):
        if self.page is None or self.y - h < BOTTOM:
            self.new_page()

    def h1(self, s):
        self.need(40)
        self.page.text(MARGIN, self.y - 22, s, 22, NAVY_900, bold=True, tag="H1")
        self.y -= 34

    def h2(self, num, s):
        self.need(52)
        self.y -= 14
        self.page.text(MARGIN, self.y - 14, "%s. %s" % (num, s), 14.5, NAVY_900,
                       bold=True, tag="H2")
        y = self.y
        self.page.artifact(lambda: self.page.line(MARGIN, y - 22, MARGIN + 46, y - 22,
                                                  GREEN_400, 2.2))
        self.y -= 32

    def h3(self, s):
        self.need(30)
        self.y -= 6
        self.page.text(MARGIN, self.y - 11, s, 10.5, NAVY_900, bold=True, tag="H3")
        self.y -= 20

    def para(self, s, color=GRAY_600, size=9.3, leading=12.4, indent=0.0):
        lines = pdfkit.wrap(s, size, TEXT_W - indent)
        self.need(len(lines) * leading + 4)
        # If it had to break to a new page, re-wrap is unnecessary: width is
        # the same on every page.
        self.y = self.page.paragraph(MARGIN + indent, self.y - 9, s, size,
                                     TEXT_W - indent, leading, color, tag="P")
        self.y -= 2

    def facts(self, rows):
        self.need(len(rows) * 13 + 14)
        self.y -= 4
        for label, value in rows:
            self.need(14)
            self.page.text(MARGIN, self.y - 9, label, 8.6, NAVY_900, bold=True, tag="P")
            self.page.text(MARGIN + 130, self.y - 9, value, 8.6, GRAY_600, tag="P")
            self.y -= 13
        self.y -= 4

    def contact(self, c):
        self.need(76)
        self.y -= 6
        top = self.y
        p = self.page
        p.artifact(lambda: (
            p.rect(MARGIN, top - 66, TEXT_W, 66, NAVY_50),
            p.rect(MARGIN, top - 66, 2.5, 66, GREEN_400),
        ))
        p.text(MARGIN + 14, top - 17, c["role"].upper(), 7.6, GREEN_700, bold=True, tag="P")
        p.text(MARGIN + 14, top - 32, c["name"], 11, NAVY_950, bold=True, tag="P")
        p.text(MARGIN + 14, top - 45, c["title"], 8.8, GRAY_600, tag="P")
        p.text(MARGIN + 260, top - 32, "Telephone  " + c["phone"], 8.8, GRAY_600, tag="P")
        p.text(MARGIN + 260, top - 45, "Email  " + c["email"], 8.8, GRAY_600, tag="P")
        self.y = top - 74


def build(logo_path=None):
    doc = pdfkit.Doc(
        title="Vidoori NASA SEWP VI Ordering Guide",
        tagged=True,
        lang="en-US",
        subject="Electronic ordering guide for the Vidoori NASA SEWP VI contract",
        fonts=FONTS,
    )
    badge = None
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as fh:
            badge = fh.read()
        doc.add_image("Badge", badge)

    f = Flow(doc)
    f.new_page()

    # ---- cover ----------------------------------------------------------
    p = f.page
    if badge:
        p.figure("Badge", MARGIN, TOP - 118, 186, 120,
                 "NASA SEWP VI Contract Holder badge issued by the NASA SEWP Program Office")
        f.y = TOP - 140
    else:
        f.y = TOP - 20

    f.h1("NASA SEWP VI Ordering Guide")
    f.para("Vidoori, Inc. - Category C, ITC/AV Mission-Based Services", NAVY_700, 11.5, 15)

    if any("[TBD" in str(v) for _, v in CONTRACT_FACTS) or "[TBD" in VERSION:
        f.y -= 6
        top = f.y
        p2 = f.page
        p2.artifact(lambda: p2.rect(MARGIN, top - 30, TEXT_W, 30, NAVY_50))
        p2.text(MARGIN + 12, top - 19, "DRAFT - NOT FOR ISSUE TO SEWP. "
                "Values shown as [TBD] await the program manager.", 9, NAVY_900,
                bold=True, tag="P")
        f.y = top - 40

    f.para("This guide explains how federal customers obtain quotes from Vidoori under the "
           "NASA SEWP VI contract, what support is provided after delivery, and how to "
           "resolve a problem with an order. It is published electronically and is suitable "
           "for downloading and printing.")
    f.para("Vidoori republishes this guide within ten business days of every contract "
           "modification. The current version is always available at vidoori.com/sewp.")
    f.facts(CONTRACT_FACTS)

    # ---- sections -------------------------------------------------------
    for sec in SECTIONS:
        f.need(120)
        f.h2(sec["n"], sec["title"])
        for kind, value in sec["blocks"]:
            if kind == "p":
                f.para(value)
            elif kind == "h3":
                f.h3(value)
            elif kind == "facts":
                f.facts(CONTRACT_FACTS)
            elif kind == "contact":
                f.contact(CONTACTS[value])

    return doc.render()


def placeholders():
    text = "".join([VERSION, EFFECTIVE, CONTRACT_NUMBER])
    text += "".join(str(v) for _, v in CONTRACT_FACTS)
    text += "".join("".join(str(x) for x in c.values()) for c in CONTACTS.values())
    for sec in SECTIONS:
        for _, v in sec["blocks"]:
            if isinstance(v, str):
                text += v
    return sorted(set(re.findall(r"\[TBD[^\]]*\]", text)))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "docs", "Vidoori_SEWP_VI_Ordering_Guide.pdf")
    logo = os.path.join(root, "tools", "sewp-badge-for-pdf.jpg")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        out = args[0]
    data = build(logo)
    pending = placeholders()

    if "--check" in sys.argv:
        problems = []
        if not os.path.exists(out):
            problems.append("%s does not exist" % os.path.relpath(out, root))
        else:
            with open(out, "rb") as fh:
                if fh.read() != data:
                    problems.append("%s is out of date - run "
                                    "python3 tools/build_sewp_ordering_guide.py"
                                    % os.path.relpath(out, root))
        if problems:
            print("%d problem(s):\n" % len(problems))
            for pr in problems:
                print("  %s" % pr)
            return 1
        print("Ordering guide is current.")
        if pending:
            print("Still a DRAFT - %d placeholder(s) awaiting the program manager:"
                  % len(pending))
            for ph in pending:
                print("  %s" % ph)
        return 0

    with open(out, "wb") as fh:
        fh.write(data)
    print("Wrote %s (%.1f KB)" % (out, len(data) / 1024.0))
    if pending:
        print("DRAFT - %d placeholder(s) awaiting the program manager:" % len(pending))
        for ph in pending:
            print("  %s" % ph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
