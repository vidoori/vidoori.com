#!/usr/bin/env python3
"""A very small PDF writer. Python 3 standard library only.

Shared by tools/build_capability_statement.py and
tools/build_sewp_ordering_guide.py so the two do not become near-copies that
drift apart — the failure mode CLAUDE.md records for contact.js/referral.js.

What it does:

  * multiple pages, one content stream each
  * the base-14 Helvetica faces, referenced rather than embedded, so nothing
    ships inside the file and the output stays small
  * JPEG images via /DCTDecode, which takes the bytes verbatim and needs no
    image decoder
  * optional PDF/UA structure tagging: a real /StructTreeRoot, marked content
    with MCIDs, a /ParentTree, /Lang, /Alt on figures, and /Artifact around
    decoration so a screen reader skips rules and background panels

Tagging is off unless you pass tagged=True to Doc().

NOTE: build_capability_statement.py still carries its own inline copy of these
primitives and does not import this module yet. That is the duplication this
module exists to prevent, so it is a deliberate, recorded debt rather than an
oversight — migrating it changes the committed PDF's bytes (different header
version and object order), which its --check would flag, so the migration
wants its own change rather than riding along with the ordering guide.
See docs/known-issues.md.

Nothing here validates conformance. Run verapdf against the result:

    verapdf -f ua1 --format text the-file.pdf
"""

import struct
import zlib

# ---------------------------------------------------------------------------
# Helvetica metrics, units per 1000. Needed because nothing here measures
# glyphs for us and text has to be wrapped before it is drawn.
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


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _xml(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# TrueType embedding.
#
# PDF/UA clause 7.21.4.1 requires every font program to be embedded, so the
# base-14 shortcut (referencing Helvetica and shipping nothing) is not an
# option for a conforming file. Liberation Sans is used because it is SIL
# Open Font Licensed, so embedding is permitted, and metric-compatible with
# Helvetica, so the width tables above stay correct and nothing reflows.
# ---------------------------------------------------------------------------

def _tables(data):
    n = struct.unpack(">H", data[4:6])[0]
    out = {}
    for i in range(n):
        off = 12 + i * 16
        tag = data[off:off + 4].decode("latin-1")
        o, l = struct.unpack(">II", data[off + 8:off + 16])
        out[tag] = (o, l)
    return out


def _cmap_unicode(data, tabs):
    """Unicode -> glyph id, from the format 4 subtable."""
    base = tabs["cmap"][0]
    ntab = struct.unpack(">H", data[base + 2:base + 4])[0]
    sub = None
    for i in range(ntab):
        pid, eid, off = struct.unpack(">HHI", data[base + 4 + i * 8:base + 12 + i * 8])
        if (pid, eid) in ((3, 1), (0, 3), (0, 4), (3, 10)):
            sub = base + off
            break
    if sub is None:
        raise ValueError("no unicode cmap subtable")
    fmt = struct.unpack(">H", data[sub:sub + 2])[0]
    if fmt != 4:
        raise ValueError("cmap format %d not supported" % fmt)
    segx2 = struct.unpack(">H", data[sub + 6:sub + 8])[0]
    seg = segx2 // 2
    ends = struct.unpack(">%dH" % seg, data[sub + 14:sub + 14 + segx2])
    sp = sub + 16 + segx2
    starts = struct.unpack(">%dH" % seg, data[sp:sp + segx2])
    dp = sp + segx2
    deltas = struct.unpack(">%dh" % seg, data[dp:dp + segx2])
    rp = dp + segx2
    ranges = struct.unpack(">%dH" % seg, data[rp:rp + segx2])
    m = {}
    for i in range(seg):
        for c in range(starts[i], min(ends[i], 0xFFFF) + 1):
            if ranges[i] == 0:
                g = (c + deltas[i]) & 0xFFFF
            else:
                gi = rp + i * 2 + ranges[i] + (c - starts[i]) * 2
                if gi + 2 > len(data):
                    continue
                g = struct.unpack(">H", data[gi:gi + 2])[0]
                if g:
                    g = (g + deltas[i]) & 0xFFFF
            if g:
                m[c] = g
    return m


def truetype_info(path):
    """Everything the PDF needs about a TrueType face."""
    with open(path, "rb") as fh:
        data = fh.read()
    tabs = _tables(data)
    ho = tabs["head"][0]
    upm = struct.unpack(">H", data[ho + 18:ho + 20])[0]
    bbox = struct.unpack(">hhhh", data[ho + 36:ho + 44])
    hh = tabs["hhea"][0]
    asc, desc = struct.unpack(">hh", data[hh + 4:hh + 8])
    nhm = struct.unpack(">H", data[hh + 34:hh + 36])[0]
    hm = tabs["hmtx"][0]
    adv = []
    for i in range(nhm):
        adv.append(struct.unpack(">H", data[hm + i * 4:hm + i * 4 + 2])[0])
    italic = struct.unpack(">i", data[tabs["post"][0] + 4:tabs["post"][0] + 8])[0] / 65536.0
    cap = asc
    if "OS/2" in tabs:
        o2 = tabs["OS/2"][0]
        ver = struct.unpack(">H", data[o2:o2 + 2])[0]
        if ver >= 2 and tabs["OS/2"][1] >= 90:
            cap = struct.unpack(">h", data[o2 + 88:o2 + 90])[0] or asc
    cmap = _cmap_unicode(data, tabs)

    def width_of(code):
        g = cmap.get(code)
        if g is None:
            return 0
        a = adv[g] if g < len(adv) else adv[-1]
        return int(round(a * 1000.0 / upm))

    s = 1000.0 / upm
    return {
        "data": data,
        "upm": upm,
        "bbox": [int(round(v * s)) for v in bbox],
        "ascent": int(round(asc * s)),
        "descent": int(round(desc * s)),
        "capheight": int(round(cap * s)),
        "italic": italic,
        "width_of": width_of,
    }


def _embed_truetype(add, path, basefont, bold=False):
    """Write the three objects a embedded TrueType face needs and return the
    /Font object number: the compressed font program, a descriptor carrying
    the metrics a reader needs when it cannot open the program, and the font
    itself with a per-code width array."""
    info = truetype_info(path)
    raw = info["data"]
    comp = zlib.compress(raw)
    file_num = add(b"<< /Length %d /Filter /FlateDecode /Length1 %d >>\nstream\n"
                   % (len(comp), len(raw)) + comp + b"\nendstream")

    # Flags bit 6 (value 32) is "non-symbolic": the face uses the standard
    # Latin character set, which is what /WinAnsiEncoding assumes.
    flags = 32
    desc = add(b"<< /Type /FontDescriptor /FontName /%s /Flags %d "
               b"/FontBBox [%d %d %d %d] /ItalicAngle %d /Ascent %d /Descent %d "
               b"/CapHeight %d /StemV %d /FontFile2 %d 0 R >>"
               % (basefont.encode(), flags,
                  info["bbox"][0], info["bbox"][1], info["bbox"][2], info["bbox"][3],
                  int(info["italic"]), info["ascent"], info["descent"],
                  info["capheight"], 160 if bold else 80, file_num))

    widths = []
    for code in range(32, 256):
        try:
            ch = bytes([code]).decode("cp1252")
        except UnicodeDecodeError:
            widths.append(0)
            continue
        widths.append(info["width_of"](ord(ch)))
    return add(b"<< /Type /Font /Subtype /TrueType /BaseFont /%s /FirstChar 32 "
               b"/LastChar 255 /Widths [%s] /FontDescriptor %d 0 R "
               b"/Encoding /WinAnsiEncoding >>"
               % (basefont.encode(), b" ".join(b"%d" % w for w in widths), desc))


# ---------------------------------------------------------------------------
# One page.
# ---------------------------------------------------------------------------

class Page:
    def __init__(self, doc, w, h):
        self.doc, self.w, self.h = doc, w, h
        self.ops = []
        self.mcid = 0          # marked-content ids restart on every page
        self.elems = []        # (struct_type, mcid, alt) in reading order

    # -- raw drawing ------------------------------------------------------

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

    def image(self, name, x, y, w, h):
        self.ops.append("q %.2f 0 0 %.2f %.2f %.2f cm /%s Do Q" % (w, h, x, y, name))

    # -- decoration -------------------------------------------------------

    def artifact(self, draw):
        """Run `draw` with its output marked as an artifact.

        PDF/UA requires that everything on the page is either tagged content
        or an artifact. Rules, panels and background fills carry no meaning
        for a screen reader and belong here.
        """
        if self.doc.tagged:
            self.ops.append("/Artifact BMC")
        draw()
        if self.doc.tagged:
            self.ops.append("EMC")

    # -- text -------------------------------------------------------------

    def text(self, x, y, s, size, color=(0, 0, 0), bold=False,
             align="left", maxw=None, tag=None):
        font = "/F2" if bold else "/F1"
        if align == "right" and maxw is not None:
            x = x + maxw - width(s, size, bold)
        elif align == "center" and maxw is not None:
            x = x + (maxw - width(s, size, bold)) / 2.0
        self.fill(color)
        body = "BT %s %.2f Tf %.2f %.2f Td (%s) Tj ET" % (font, size, x, y, esc(s))
        if self.doc.tagged and tag:
            mcid = self.mcid
            self.mcid += 1
            self.elems.append((tag, mcid, None))
            self.ops.append("/%s <</MCID %d>> BDC" % (tag, mcid))
            self.ops.append(body)
            self.ops.append("EMC")
        elif self.doc.tagged:
            self.ops.append("/Artifact BMC")
            self.ops.append(body)
            self.ops.append("EMC")
        else:
            self.ops.append(body)

    def paragraph(self, x, y, s, size, maxw, leading, color=(0, 0, 0),
                  bold=False, tag=None):
        """A wrapped block. Tagged as ONE element, not one per line, so a
        screen reader reads it as a paragraph rather than a list of lines."""
        lines = wrap(s, size, maxw, bold)
        if self.doc.tagged and tag:
            mcid = self.mcid
            self.mcid += 1
            self.elems.append((tag, mcid, None))
            self.ops.append("/%s <</MCID %d>> BDC" % (tag, mcid))
        self.fill(color)
        font = "/F2" if bold else "/F1"
        for ln in lines:
            self.ops.append("BT %s %.2f Tf %.2f %.2f Td (%s) Tj ET"
                            % (font, size, x, y, esc(ln)))
            y -= leading
        if self.doc.tagged and tag:
            self.ops.append("EMC")
        return y

    def figure(self, name, x, y, w, h, alt):
        """A tagged image. /Alt is what a screen reader announces."""
        if self.doc.tagged:
            mcid = self.mcid
            self.mcid += 1
            self.elems.append(("Figure", mcid, alt))
            self.ops.append("/Figure <</MCID %d>> BDC" % mcid)
            self.image(name, x, y, w, h)
            self.ops.append("EMC")
        else:
            self.image(name, x, y, w, h)

    def content(self):
        return "\n".join(self.ops).encode("latin-1")


# ---------------------------------------------------------------------------
# The document.
# ---------------------------------------------------------------------------

class Doc:
    def __init__(self, title, tagged=False, lang="en-US", author="Vidoori, Inc.",
                 subject="", fonts=None):
        """fonts: {"F1": regular.ttf, "F2": bold.ttf}. Given, the faces are
        embedded, which PDF/UA requires. Omitted, the base-14 Helvetica names
        are referenced instead - smaller, but never conforming."""
        self.title, self.tagged, self.lang = title, tagged, lang
        self.author, self.subject = author, subject
        self.fonts = fonts or {}
        self.pages = []
        self.images = {}       # name -> jpeg bytes

    def page(self, w=612, h=792):
        p = Page(self, w, h)
        self.pages.append(p)
        return p

    def add_image(self, name, jpeg_bytes):
        self.images[name] = jpeg_bytes

    def render(self):
        objs = []

        def add(body):
            objs.append(body)
            return len(objs)

        if self.fonts:
            font_reg = _embed_truetype(add, self.fonts["F1"], "LiberationSans", bold=False)
            font_bold = _embed_truetype(add, self.fonts["F2"], "LiberationSans-Bold", bold=True)
        else:
            font_reg = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                           b"/Encoding /WinAnsiEncoding >>")
            font_bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                            b"/Encoding /WinAnsiEncoding >>")

        img_refs = {}
        for name, data in self.images.items():
            iw, ih = jpeg_size(data)
            img_refs[name] = add(
                b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
                b"/Length %d >>\nstream\n" % (iw, ih, len(data)) + data + b"\nendstream")

        xobj = b""
        if img_refs:
            xobj = b"/XObject << " + b" ".join(
                b"/%s %d 0 R" % (n.encode(), r) for n, r in img_refs.items()) + b" >>"
        resources = (b"<< /Font << /F1 %d 0 R /F2 %d 0 R >> " % (font_reg, font_bold)
                     + xobj + b" >>")

        # Reserve numbers for the page tree and structure root so pages can
        # reference their parent before those objects exist.
        contents, page_nums = [], []
        for pg in self.pages:
            s = zlib.compress(pg.content())
            contents.append(add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n"
                                % len(s) + s + b"\nendstream"))
        pages_num = len(objs) + len(self.pages) + 1
        for i, pg in enumerate(self.pages):
            extra = b""
            if self.tagged:
                extra = b"/StructParents %d " % i
            page_nums.append(add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Resources %s "
                b"%s/Contents %d 0 R >>"
                % (pages_num, pg.w, pg.h, resources, extra, contents[i])))
        pages_obj = add(b"<< /Type /Pages /Kids [" +
                        b" ".join(b"%d 0 R" % n for n in page_nums) +
                        b"] /Count %d >>" % len(page_nums))
        assert pages_obj == pages_num, "page tree object number drifted"

        struct_root = b""
        if self.tagged:
            # One StructElem per marked-content item, gathered under a single
            # /Document element. /ParentTree maps each page's StructParents
            # index to the elements drawn on it, which PDF/UA requires.
            # Every object here references one added later, so the numbers are
            # worked out before anything is written: elements point at the
            # /Document element as their parent, and /Document points at the
            # /StructTreeRoot. Getting this wrong produces a file that opens
            # fine and fails validation, so the arithmetic is asserted below.
            total_elems = sum(len(pg.elems) for pg in self.pages)
            base = len(objs)
            doc_elem_num = base + total_elems + 1
            parent_tree_num = doc_elem_num + 1
            struct_root_num = doc_elem_num + 2

            elem_nums = []          # list per page
            for i, pg in enumerate(self.pages):
                nums = []
                for (stype, mcid, alt) in pg.elems:
                    body = (b"<< /Type /StructElem /S /%s /P %d 0 R /Pg %d 0 R /K %d"
                            % (stype.encode(), doc_elem_num, page_nums[i], mcid))
                    if alt:
                        body += b" /Alt (" + esc(alt).encode("latin-1") + b")"
                    body += b" >>"
                    nums.append(add(body))
                elem_nums.append(nums)
            actual_doc = add(b"<< /Type /StructElem /S /Document /P %d 0 R /K ["
                             % struct_root_num +
                             b" ".join(b"%d 0 R" % n
                                       for nums in elem_nums for n in nums) +
                             b"] >>")
            assert actual_doc == doc_elem_num, "structure element numbering drifted"

            parent_pairs = []
            for i, nums in enumerate(elem_nums):
                parent_pairs.append(b"%d [" % i +
                                    b" ".join(b"%d 0 R" % n for n in nums) + b"]")
            actual_pt = add(b"<< /Nums [" + b" ".join(parent_pairs) + b"] >>")
            assert actual_pt == parent_tree_num, "parent tree object number drifted"
            actual_sr = add(b"<< /Type /StructTreeRoot /K [%d 0 R] "
                            b"/ParentTree %d 0 R /ParentTreeNextKey %d >>"
                            % (doc_elem_num, parent_tree_num, len(self.pages)))
            assert actual_sr == struct_root_num, "structure root object number drifted"
            struct_root = (b"/StructTreeRoot %d 0 R /MarkInfo << /Marked true >> "
                           b"/Lang (%s) /ViewerPreferences << /DisplayDocTitle true >> "
                           % (struct_root_num, self.lang.encode()))

        # PDF/UA requires an XMP metadata stream in the catalog declaring the
        # conformance level, and the title has to appear here as well as in
        # /Info or clause 7.1 fails.
        meta_ref = b""
        if self.tagged:
            xmp = ('<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>'
                   '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
                   '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                   '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
                   '<dc:title><rdf:Alt><rdf:li xml:lang="x-default">%s</rdf:li></rdf:Alt></dc:title>'
                   '<dc:creator><rdf:Seq><rdf:li>%s</rdf:li></rdf:Seq></dc:creator>'
                   '</rdf:Description>'
                   '<rdf:Description rdf:about="" xmlns:pdfuaid="http://www.aiim.org/pdfua/ns/id/">'
                   '<pdfuaid:part>1</pdfuaid:part></rdf:Description>'
                   '<rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">'
                   '<pdf:Producer>vidoori.com tools/pdfkit.py</pdf:Producer></rdf:Description>'
                   '</rdf:RDF></x:xmpmeta><?xpacket end="w"?>'
                   % (_xml(self.title), _xml(self.author))).encode("utf-8")
            meta_num = add(b"<< /Type /Metadata /Subtype /XML /Length %d >>\nstream\n" % len(xmp)
                           + xmp + b"\nendstream")
            meta_ref = b"/Metadata %d 0 R " % meta_num

        catalog = add(b"<< /Type /Catalog /Pages %d 0 R " % pages_obj
                      + meta_ref + struct_root + b">>")
        info = add(b"<< /Title (" + esc(self.title).encode("latin-1") + b") "
                   b"/Author (" + esc(self.author).encode("latin-1") + b") "
                   b"/Subject (" + esc(self.subject).encode("latin-1") + b") "
                   b"/Creator (vidoori.com tools/pdfkit.py) >>")

        out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref_at = len(out)
        out += b"xref\n0 %d\n" % (len(objs) + 1)
        out += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            out += b"%010d 00000 n \n" % off
        out += (b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objs) + 1, catalog, info, xref_at))
        return bytes(out)
