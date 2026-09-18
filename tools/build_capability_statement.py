#!/usr/bin/env python3
"""Generate the Vidoori capabilities statement as a one-page PDF.

Python 3 standard library only, like tools/build.py — no reportlab, no
wkhtmltopdf, nothing to install. The PDF is written by hand: a page tree, one
content stream of drawing operators, the base-14 Helvetica fonts (which every
reader has, so nothing is embedded), and the logo as a JPEG XObject with
/DCTDecode, which lets the JPEG bytes go in untouched rather than needing an
image decoder.

    python3 tools/build_capability_statement.py

tools/logo-for-pdf.jpg is the committed logo artwork. It is a JPEG because a
JPEG can be dropped into a PDF verbatim; anything else would need decoding.
Regenerate it from the brand original with:

    sips -s format jpeg -s formatOptions 92 --resampleWidth 600 \
         --padToHeightWidth 200 600 --padColor FFFFFF \
         assets/img/vidoori-logo.svg --out tools/logo-for-pdf.jpg

Writes assets/docs/Vidoori_CapabilityStatement.pdf. Pass a path to write
elsewhere. Facts live in the CONTENT block below — edit that, not the drawing
code. Anything here that also appears on the site must agree with it; see
docs/content-catalog.md, which is the inventory of record.

Note PDFs carry no ?v= cache stamp, unlike site.css and site.js. Replacing
this file in place means Cloudflare's edge may serve the old document for a
while. Ship under a new filename if a revision has to reach people at once.
"""

import html as html_mod
import os
import re
import struct
import sys
import zlib

# ---------------------------------------------------------------------------
# Content. Edit this, not the drawing code below.
# ---------------------------------------------------------------------------

REVISION = "September 2026"

LEAD = (
    "Vidoori, Inc. is a consulting firm providing high quality information technology "
    "services and products that solve real business problems for Government and Commercial "
    "clients. The Vidoori approach uses an unyielding focus on achieving measurable results, "
    "reducing cost, and introducing innovative solutions built on industry best practices."
)

POINT_OF_CONTACT = [
    ("Haley Kubal", True),
    ("Contract Manager", False),
    ("(240) 608-6810", False),
    ("contracts@vidoori.com", False),
]

COMPANY_INFO = [
    "UEI: N37JST95C3S5",
    "CAGE Code: 6T0A7",
    "EIN/TIN: 26-3184467",
]

CERTIFICATIONS = [
    "CMMI V3.0 Level 3 - appraised for",
    "Development and Services",
    "ISO 9001:2015",
    "ISO/IEC 20000-1:2018",
    "DCAA-compliant accounting",
]

CONTRACT_VEHICLES = [
    "GSA MAS - GS-35F-335CA",
    "SeaPort-NxG",
    "FAA eFAST - 693KA9-22-A-00186",
    "NASA SEWP VI - Category C",
]

# NAICS. Taken from the SAM.gov registration on 2026-09-18, which is the
# authoritative list. Two codes the sheet carried before that date were NAICS
# 2017 spellings retired in the 2022 revision: 519190 became 519290, and 811212
# was consolidated into 811210. 488119 (Other Airport Operations) is held but
# deliberately not advertised here - it reads oddly on an IT capability sheet.
NAICS_PRIMARY = "541512"
NAICS_OTHER = [
    "513210", "518210", "519290", "541330", "541511",
    "541513", "541519", "541715", "611420", "811210",
]
NAICS_ALL = [NAICS_PRIMARY] + NAICS_OTHER

COMPETENCIES = [
    ("Integration & Test", [
        "Test Strategy & Planning",
        "Test Automation",
        "End to End Testing",
        "Interface Testing",
        "Hardware Testing",
        "Manual Testing",
        "Accessibility (Section 508)",
        "Performance Testing",
        "Data Validation",
    ]),
    ("DevSecOps", [
        "Secure Coding Practices",
        "Automated Security Testing",
        "CI/CD Pipeline Security",
        "Infrastructure Security",
        "Threat Modeling",
        "Security Modeling",
        "Security Training & Awareness",
        "Secure Cloud Adoption",
        "Secure Configuration Mgmt",
    ]),
    ("Cloud-Native", [
        "Application Modernization",
        "Cloud Architecture & Development",
        "Microservices & Containers",
        "Cloud Platforms (AWS, Azure)",
        "Automation",
        "Mobile Development",
    ]),
    ("Software Development", [
        "Architecture & Design",
        "Custom Application Development",
        "Mobile Platform Development",
        "Database Management & Dev",
        "Data Integration",
        "Application Modernization",
    ]),
]

PAST_PERFORMANCE = [
    ("Department of Commerce, U.S. Census Bureau",
     "Provided integration and testing services for 64+ integrated systems involved in the 2020 "
     "US Census. Also implemented an enterprise level Test Center of Excellence to provide "
     "testing (functional, integration, accessibility, automation, performance) as a service to "
     "support enterprise testing needs, including 30+ national U.S. Surveys. Additionally, "
     "provided custom development (web and mobile) to support internet responses along with "
     "integrated custom SharePoint applications and dashboards."),
    ("Department of Veterans Affairs",
     "Provided software development, testing and deployment management services for the Project "
     "Management Accountability System (PMAS). This enabled PMs across the U.S. to centrally "
     "manage over $500M in projects. Also developed a custom OMB submission tool that reduced "
     "submission time and errors by over 55%."),
    ("Department of the Navy, NAVSUP",
     "Provided cybersecurity, training, RMF and database services. This enables the Navy to "
     "ensure that compliance is maintained and supports the mission of assured continuity of "
     "operations for the warfighter."),
]

DIFFERENTIATORS = [
    "DCAA audit compliance",
    "CMMI and ISO certified",
    "Seasoned management team with domestic and international project delivery experience",
    "Proven, cost effective VPT performance testing software",
    "Turnkey integrated SharePoint dashboards for real-time metrics and reporting",
    "Mature, proven framework for implementing a Test Center of Excellence to provide testing "
    "as a service",
    "Client management portal providing real-time status updates for contracting officers",
    "Vidoori Applied Innovation Lab (VAIL): an internal R&D and applied-AI lab that develops "
    "reusable intellectual property and prepares engineers for contract delivery",
    "Dedicated quality assurance team that reviews all programs and projects on a consistent basis",
    "Custom OMB submission tool proven to reduce submission time and errors",
    "Internal employee engagement team focused on career growth and retention",
]

FOOTER = ("Corporate Headquarters: 4000 Garden City Drive, Suite 808, Hyattsville, MD 20785"
          "   |   (240) 608-6810   |   www.vidoori.com")

# ---------------------------------------------------------------------------
# Brand tokens, taken from the ramps in assets/css/site.css.
# ---------------------------------------------------------------------------

NAVY_950 = (0.078, 0.082, 0.169)   # #14152b
NAVY_900 = (0.114, 0.118, 0.235)   # #1d1e3c
NAVY_700 = (0.255, 0.263, 0.447)   # #414372
NAVY_200 = (0.788, 0.796, 0.875)   # #c9cbdf
NAVY_100 = (0.902, 0.906, 0.941)   # #e6e7f0
NAVY_50 = (0.957, 0.957, 0.976)    # #f4f4f9
GREEN_400 = (0.604, 0.827, 0.537)  # #9ad389
GREEN_700 = (0.247, 0.478, 0.173)  # #3f7a2c
GRAY_600 = (0.357, 0.376, 0.439)   # #5b6070
WHITE = (1, 1, 1)

# ---------------------------------------------------------------------------
# Helvetica metrics (units per 1000). Needed to wrap text, since nothing here
# measures glyphs for us.
# ---------------------------------------------------------------------------

_REG = {
    ' ': 278, '!': 278, '"': 355, '#': 556, '$': 556, '%': 889, '&': 667, "'": 191,
    '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
    ':': 278, ';': 278, '<': 584, '=': 584, '>': 584, '?': 556, '@': 1015,
    '[': 278, '\\': 278, ']': 278, '^': 469, '_': 556, '`': 333,
    '{': 334, '|': 260, '}': 334, '~': 584,
    'A': 667, 'B': 667, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722,
    'I': 278, 'J': 500, 'K': 667, 'L': 556, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667,
    'Y': 667, 'Z': 611,
    'a': 556, 'b': 556, 'c': 500, 'd': 556, 'e': 556, 'f': 278, 'g': 556, 'h': 556,
    'i': 222, 'j': 222, 'k': 500, 'l': 222, 'm': 833, 'n': 556, 'o': 556, 'p': 556,
    'q': 556, 'r': 333, 's': 500, 't': 278, 'u': 556, 'v': 500, 'w': 722, 'x': 500,
    'y': 500, 'z': 500,
}
_BOLD = {
    ' ': 278, '!': 333, '"': 474, '#': 556, '$': 556, '%': 889, '&': 722, "'": 238,
    '(': 333, ')': 333, '*': 389, '+': 584, ',': 278, '-': 333, '.': 278, '/': 278,
    ':': 333, ';': 333, '<': 584, '=': 584, '>': 584, '?': 611, '@': 975,
    '[': 333, '\\': 278, ']': 333, '^': 584, '_': 556, '`': 333,
    '{': 389, '|': 280, '}': 389, '~': 584,
    'A': 722, 'B': 722, 'C': 722, 'D': 722, 'E': 667, 'F': 611, 'G': 778, 'H': 722,
    'I': 278, 'J': 556, 'K': 722, 'L': 611, 'M': 833, 'N': 722, 'O': 778, 'P': 667,
    'Q': 778, 'R': 722, 'S': 667, 'T': 611, 'U': 722, 'V': 667, 'W': 944, 'X': 667,
    'Y': 667, 'Z': 611,
    'a': 556, 'b': 611, 'c': 556, 'd': 611, 'e': 556, 'f': 333, 'g': 611, 'h': 611,
    'i': 278, 'j': 278, 'k': 556, 'l': 278, 'm': 889, 'n': 611, 'o': 611, 'p': 611,
    'q': 611, 'r': 389, 's': 556, 't': 333, 'u': 611, 'v': 556, 'w': 778, 'x': 556,
    'y': 556, 'z': 500,
}
for _d in (_REG, _BOLD):
    for _c in "0123456789":
        _d[_c] = 556


def width(text, size, bold=False):
    table = _BOLD if bold else _REG
    return sum(table.get(ch, 556) for ch in text) * size / 1000.0


def wrap(text, size, max_width, bold=False):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if width(trial, size, bold) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------------
# A very small PDF writer.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w=612, h=792):
        self.w, self.h, self.ops = w, h, []

    def _esc(self, s):
        return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    def fill(self, c):
        self.ops.append("%.4f %.4f %.4f rg" % c)

    def stroke_color(self, c):
        self.ops.append("%.4f %.4f %.4f RG" % c)

    def rect(self, x, y, w, h, color):
        self.fill(color)
        self.ops.append("%.2f %.2f %.2f %.2f re f" % (x, y, w, h))

    def line(self, x1, y1, x2, y2, color, lw=0.6):
        self.stroke_color(color)
        self.ops.append("%.2f w" % lw)
        self.ops.append("%.2f %.2f m %.2f %.2f l S" % (x1, y1, x2, y2))

    def text(self, x, y, s, size, color=NAVY_950, bold=False, align="left", maxw=None):
        font = "/F2" if bold else "/F1"
        if align == "right" and maxw is not None:
            x = x + maxw - width(s, size, bold)
        elif align == "center" and maxw is not None:
            x = x + (maxw - width(s, size, bold)) / 2.0
        self.fill(color)
        self.ops.append("BT %s %.2f Tf %.2f %.2f Td (%s) Tj ET"
                        % (font, size, x, y, self._esc(s)))

    def paragraph(self, x, y, s, size, maxw, leading, color=NAVY_950, bold=False):
        for ln in wrap(s, size, maxw, bold):
            self.text(x, y, ln, size, color, bold)
            y -= leading
        return y

    def image(self, name, x, y, w, h):
        self.ops.append("q %.2f 0 0 %.2f %.2f %.2f cm /%s Do Q" % (w, h, x, y, name))

    def content(self):
        return "\n".join(self.ops).encode("latin-1")


def jpeg_size(data):
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + seglen
    raise ValueError("no JPEG frame header found")


def render_pdf(canvas, logo_bytes=None):
    objects = []

    def add(body):
        objects.append(body)
        return len(objects)  # object numbers are 1-based

    stream = zlib.compress(canvas.content())
    content_obj = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream)
                      + stream + b"\nendstream")
    font_reg = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                   b"/Encoding /WinAnsiEncoding >>")
    font_bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                    b"/Encoding /WinAnsiEncoding >>")

    xobject = b""
    if logo_bytes:
        lw, lh = jpeg_size(logo_bytes)
        img = add(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                  b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
                  b"/Length %d >>\nstream\n" % (lw, lh, len(logo_bytes))
                  + logo_bytes + b"\nendstream")
        xobject = b"/XObject << /Logo %d 0 R >>" % img

    resources = (b"<< /Font << /F1 %d 0 R /F2 %d 0 R >> " % (font_reg, font_bold)
                 + xobject + b" >>")
    pages_num = len(objects) + 2  # page object is next, pages object after it
    page = add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Resources %s "
               b"/Contents %d 0 R >>" % (pages_num, canvas.w, canvas.h, resources, content_obj))
    pages = add(b"<< /Type /Pages /Kids [%d 0 R] /Count 1 >>" % page)
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages)
    info = add(b"<< /Title (Vidoori Capabilities Statement) /Author (Vidoori, Inc.) "
               b"/Subject (Capabilities statement) /Creator "
               b"(tools/build_capability_statement.py) >>")

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"

    xref_at = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, catalog, info, xref_at))

    return bytes(out)


# ---------------------------------------------------------------------------
# Layout.
# ---------------------------------------------------------------------------

def band(c, x, y, w, label):
    """Section header: a filled navy bar with a chevron, as on the original."""
    c.rect(x, y, w, 15, NAVY_700)
    c.ops.append("%.4f %.4f %.4f rg" % NAVY_700)
    c.ops.append("%.2f %.2f m %.2f %.2f l %.2f %.2f l f"
                 % (x + w, y, x + w + 9, y + 7.5, x + w, y + 15))
    c.text(x + 9, y + 4.5, label.upper(), 8.5, WHITE, bold=True)


def build(logo_path=None):
    c = Canvas()
    M = 36.0
    RIGHT = c.w - M
    W = RIGHT - M

    # ---- header -----------------------------------------------------------
    logo_bytes = None
    top = c.h - M                      # 756: the top of the content area
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as fh:
            logo_bytes = fh.read()
        c.image("Logo", M, top - 50, 150, 50)
    else:
        c.text(M, top - 34, "Vidoori", 26, NAVY_700, bold=True)
    c.text(M, top - 33, "CAPABILITIES STATEMENT", 19, NAVY_900, bold=True,
           align="right", maxw=W)
    c.line(M, top - 60, RIGHT, top - 60, NAVY_200, 0.8)

    # ---- lead -------------------------------------------------------------
    y = c.paragraph(M, top - 74, LEAD, 9.2, W, 12.4, GRAY_600)

    # ---- company snapshot -------------------------------------------------
    y -= 8
    box_h = 150.0
    box_top = y
    c.rect(M, box_top - box_h, W, box_h, NAVY_50)
    c.rect(M, box_top - box_h, 3, box_h, GREEN_400)
    c.text(M + 12, box_top - 17, "COMPANY SNAPSHOT", 9.5, NAVY_900, bold=True)

    col = [M + 12, M + 200, M + 382]
    colw = [176, 172, 158]
    ty = box_top - 36

    def head(x, yy, s):
        c.text(x, yy, s, 7.6, GREEN_700, bold=True)
        return yy - 11.5

    # column 1
    yy = head(col[0], ty, "POINT OF CONTACT")
    for line, bold in POINT_OF_CONTACT:
        c.text(col[0], yy, line, 8.4, NAVY_950 if bold else GRAY_600, bold=bold)
        yy -= 11
    yy = head(col[0], yy - 3, "COMPANY INFORMATION")
    for line in COMPANY_INFO:
        c.text(col[0], yy, line, 8.4, GRAY_600)
        yy -= 11

    # column 2
    yy = head(col[1], ty, "CERTIFICATIONS")
    for line in CERTIFICATIONS:
        c.text(col[1], yy, line, 8.4, GRAY_600)
        yy -= 11

    # column 3
    yy = head(col[2], ty, "CONTRACT VEHICLES")
    for line in CONTRACT_VEHICLES:
        c.text(col[2], yy, line, 8.4, GRAY_600)
        yy -= 11
    yy = head(col[2], yy - 3, "NAICS CODES")
    c.text(col[2], yy, "%s (primary)" % NAICS_PRIMARY, 8.4, NAVY_950, bold=True)
    yy -= 11
    for line in wrap(", ".join(NAICS_OTHER), 8.4, colw[2]):
        c.text(col[2], yy, line, 8.4, GRAY_600)
        yy -= 11

    y = box_top - box_h - 14

    # ---- core competencies ------------------------------------------------
    band(c, M, y, 152, "Core Competencies")
    y -= 20
    cw = (W - 3 * 10) / 4.0
    ctop = y
    for i, (title, items) in enumerate(COMPETENCIES):
        x = M + i * (cw + 10)
        yy = ctop
        c.text(x, yy, title, 9.8, NAVY_900, bold=True)
        yy -= 14
        for item in items:
            for ln in wrap(item, 8.5, cw):
                c.text(x, yy, ln, 8.5, GRAY_600)
                yy -= 10.6
    y = ctop - 14 - 10.6 * 9 - 20

    # ---- past performance (left) and differentiators (right) --------------
    split = M + W * 0.545
    lw = split - M - 14
    rx = split + 6
    rw = RIGHT - rx

    band(c, M, y, 136, "Past Performance")
    band(c, rx, y, 122, "Differentiators")
    y -= 20

    ly = y
    for title, body in PAST_PERFORMANCE:
        c.text(M, ly, title.upper(), 8.9, NAVY_900, bold=True)
        ly -= 12
        ly = c.paragraph(M, ly, body, 8.6, lw, 10.3, GRAY_600)
        ly -= 9

    ry = y
    for item in DIFFERENTIATORS:
        c.rect(rx + 2, ry + 2.6, 3, 3, GREEN_700)
        lines = wrap(item, 8.6, rw - 10)
        for j, ln in enumerate(lines):
            c.text(rx + 10, ry, ln, 8.6, GRAY_600)
            ry -= 10.3
        ry -= 2.8

    # ---- footer -----------------------------------------------------------
    fy = 40.0
    c.line(M, fy + 16, RIGHT, fy + 16, NAVY_200, 0.8)
    c.text(M, fy + 4, FOOTER, 8, NAVY_700)
    c.text(M, fy - 8, "Revised %s" % REVISION, 7, GRAY_600)
    c.text(M, fy - 8, "Vidoori, Inc.", 7, GRAY_600, align="right", maxw=W)

    return render_pdf(c, logo_bytes), ly, ry


# ---------------------------------------------------------------------------
# Agreement with the site.
#
# The PDF and the website state the same facts in two places, which is exactly
# how they drifted apart before: the sheet advertised a retired contract
# vehicle and a capability page that no longer existed. These checks are what
# stops that happening silently a second time. They read the *built* HTML, so
# run tools/build.py first.
# ---------------------------------------------------------------------------

def check_against_site(root):
    problems = []

    def read(rel):
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            problems.append("missing built page %s - run tools/build.py first" % rel)
            return ""
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    vehicles = read("who-we-are/contract-vehicles/index.html")
    practices = read("what-we-do/index.html")

    # Contract vehicles: one record per vehicle on the page, NAICS excluded.
    site_v = [html_mod.unescape(m) for m in
              re.findall(r'<div class="record">.*?<h3>(.*?)</h3>', vehicles, re.S)]
    site_v = [v for v in site_v if v.strip().lower() != "naics codes"]
    pdf_v = [v.split(" - ")[0].strip() for v in CONTRACT_VEHICLES]
    if sorted(site_v) != sorted(pdf_v):
        problems.append("contract vehicles disagree\n"
                        "      PDF:  %s\n      site: %s"
                        % (", ".join(pdf_v) or "(none)", ", ".join(site_v) or "(none)"))

    # Core competencies must be the practices the site actually publishes.
    site_p = [html_mod.unescape(m) for m in
              re.findall(r'<h3><a href="/what-we-do/[^"]+/">(.*?)</a></h3>', practices)]
    pdf_p = [title for title, _ in COMPETENCIES]
    if sorted(site_p) != sorted(pdf_p):
        problems.append("core competencies disagree with /what-we-do/\n"
                        "      PDF:  %s\n      site: %s"
                        % (", ".join(pdf_p) or "(none)", ", ".join(site_p) or "(none)"))

    # Identifiers the sheet prints must be findable on the site.
    for value in ("N37JST95C3S5", "6T0A7"):
        if value not in vehicles:
            problems.append("%s is on the PDF but not on /who-we-are/contract-vehicles/" % value)
    for code in NAICS_ALL:
        if code not in vehicles:
            problems.append("NAICS %s is on the PDF but not on "
                            "/who-we-are/contract-vehicles/" % code)

    return problems


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(root, "assets", "docs", "Vidoori_CapabilityStatement.pdf")
    logo = os.path.join(root, "tools", "logo-for-pdf.jpg")
    args = [a for a in sys.argv[1:] if a != "--check"]
    checking = "--check" in sys.argv
    out = args[0] if args else default_out
    if len(args) > 1:
        logo = args[1]

    data, ly, ry = build(logo)
    problems = check_against_site(root)

    if checking:
        if not os.path.exists(out):
            problems.insert(0, "%s does not exist" % os.path.relpath(out, root))
        else:
            with open(out, "rb") as fh:
                if fh.read() != data:
                    problems.insert(0, "%s is out of date - run "
                                    "python3 tools/build_capability_statement.py"
                                    % os.path.relpath(out, root))
        if min(ly, ry) < 58:
            problems.append("content overruns the footer rule")
        if problems:
            print("%d problem(s):\n" % len(problems))
            for p in problems:
                print("  %s" % p)
            return 1
        print("Capability statement is current and agrees with the site.")
        return 0

    with open(out, "wb") as fh:
        fh.write(data)
    print("Wrote %s (%.1f KB)" % (out, len(data) / 1024.0))
    print("Column baselines: past performance %.1f pt, differentiators %.1f pt "
          "(footer rule sits at 56 pt)" % (ly, ry))
    for p in problems:
        print("  WARNING: %s" % p)
    if min(ly, ry) < 58:
        print("WARNING: content overruns the footer - trim a bullet or reduce leading.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
