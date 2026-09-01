# vidoori.com — Content Catalog

What the site contains, section by section. Use it to answer "do we already say this
somewhere?" and "where does this fact live?" without opening 41 files.

Everything below describes the **current** static site. The legacy WordPress snapshot that
the rebuild was derived from is preserved in [Appendix: legacy capture](#appendix-legacy-capture-2026-08-28)
at the bottom — it is the rationale for the rules in `_redirects` and should not be edited.

> Facts here are duplicated from `_src/`, so they can drift. `_src/` wins. When you change
> copy that this file records, update it in the same commit.

## Brand palette (from `logos/*.svg` — the only authoritative source we control)

| Token | Hex | Role in logo |
|---|---|---|
| Navy / indigo | `#414372` | Wordmark + badge body (primary) |
| Periwinkle | `#BAC0D1` | Secondary / muted accent |
| Green | `#9AD389` | Accent highlight |

## Site structure (41 pages: 23 pages + 18 posts)

### Primary nav (`_src/site.json`)
- **Who We Are** — `/who-we-are/`
  - Our Company, Leadership, Our Values, Corporate Culture, Certifications,
    Awards & Recognition, Contract Vehicles
- **What We Do** — `/what-we-do/`
  - All Capabilities, Integration & Test, DevSecOps, Cloud-Native, Data Management,
    Software Development, Cybersecurity, Intelligence, Strategy
- **Solutions** — VPT Performance Testing (`https://vpt.vidoori.com/about`, external) — the
  only entry in this group
- **Insights** — `/insights/`
- **Careers** — `/careers/`

`/contact/`, `/privacy-policy/`, and `/terms-of-use/` are reachable from the footer and body
copy rather than the primary nav.

## Key content

### Positioning
- Tagline: **"We are dedicated to our client's mission."** (`_src/site.json`, and the home `<h1>`)
- Boilerplate: "Vidoori is a consulting firm providing high quality information technology
  services and products that solve real business problems for Government and Commercial clients."
- Secondary: "We are solution focused and people driven." (the `/who-we-are/` `<h1>`) / "Delivering Excellence"
- Founded 2008 by Trong Khuong Bui.

### Contact / corporate
- Corporate Office: 4000 Garden City Drive, Suite 808, Hyattsville, MD 20785
- `info@vidoori.com` · `contracts@vidoori.com` · Phone (240) 608-6810 · Fax (240) 331-0304
- HQ Hyattsville MD; satellite locations in Washington D.C., Maryland, Virginia
- Twitter/X: `@vidooriinc` · LinkedIn: `company/vidoori-inc`
- Careers ATS: `https://vidoori.teamtailor.com/jobs` (external)
- VPT product: `https://vpt.vidoori.com/about` (external)

All of the above live in `_src/site.json` and are injected into the footer and JSON-LD — change
them there, not in page copy.

### Certifications
- CMMI® v3.0 Maturity Level 3 — Development **and** Services (published appraisal 75593)
- ISO 9001:2015 + ISO/IEC 20000-1:2018, certified by NSF
- DCAA-compliant accounting system

### Contract vehicles
| Vehicle | Contract # | Notes |
|---|---|---|
| GSA MAS | `GS-35F-335CA` | Contract Manager: Haley Kubal, contracts@vidoori.com |
| GSA 8(a) STARS III | `47QTCB22D0131` | Includes Emerging Technologies sub-area |
| SeaPort NxG | — | Navy; Engineering + Program Management Services |

UEI: `N37JST95C3S5` · CAGE: `6T0A7`

### Awards (6)
- Washington Business Journal 50 Fastest Growing — No. 32 (2020)
- Inc. 5000 (US) — No. 607 (2020), 2 consecutive years
- Fast 100 Asian American Business — 2020, 2 consecutive years
- Financial Times America's Fastest Growing — top 100, US Technology sector (2020)
- Inc. 5000 Washington D.C. Metro — No. 22 (2019)
- Largest Cybersecurity Companies in Greater Washington — No. 13 (2021), WBJ, on 2020 revenue

### Values (8)
The Best People · Ethics and Integrity · Innovation · Collaboration · Value and Quality ·
Support the Greater Good · Diversity and Inclusion · Health, Safety and Well-Being

### Benefits (Corporate Culture)
Medical/dental/vision (employee + family) · Life insurance · Fully vested 401(k) + match ·
Performance bonuses · Corporate events · HSA · Disability insurance · Generous PTO ·
Learning opportunities

### Services — capability lists as published
- **Integration & Test**: Test Strategy & Planning, End to End Testing, Hardware Testing,
  Accessibility (Section 508), Data Validation, Test Automation, Interface Testing,
  Manual Testing, Performance Testing.
  Hook: the 1:10:100 Quality Rule. IV&V methodology. VPT platform.
- **DevSecOps**: Secure Coding Practices, CI/CD Pipeline Security, Threat Modeling, Security
  Training and Awareness, Secure Configuration Management, Automated Security Testing,
  Infrastructure Security, Security Modeling, Secure Cloud Adoption.
  Three offer shapes: Consulting, Operational, DevSecOps-as-a-Service (AWS/Azure/GCP).
- **Cloud-Native**: Application Modernization, Microservices & Containers, Automation,
  Cloud Architecture & Development, Cloud Platforms (AWS, Azure), Mobile Development.
  Sub-themes: Architecture & Design, Development, Management.
- **Data Management**: Data Quality Analysis, Synthetic Data Generation, Integrated Dashboards,
  Data Science, Custom O365 & SharePoint Integration, Business Intelligence Dashboards,
  Data Privacy and Security, Multiple Data Source Integration, Data Governance.
- **Software Development**: Architecture & Design, Mobile Platform Development, Data Integration,
  Custom Application Development, Database Management & Development, Application Modernization.
- **Cybersecurity**: right-sized solutions, how we work, an expanded network. Offensive and
  defensive threat protection; APT mitigation; Information Assurance compliance.
- **Intelligence**: two solution areas — Integrated business intelligence, Portfolio investment
  management.
- **Strategy**: consulting narrative only, no capability list.

### Leadership (`/who-we-are/leadership/`)
| Name | Title |
|---|---|
| Trong Khuong Bui | Founder & Chief Executive Officer |
| Eric Huang | Chief Strategy Officer |

There is no Board of Advisors section. Individual bio URLs do not exist; the ten legacy
`/who-we-are/leadership/<name>` paths all 301 to the single page.

### Insights — 18 posts
Category path segments in use: `news`, `cybersecurity`, `data`, `test-integration`,
`cloud-native`, `innovations`. No publish dates are exposed anywhere on the site.

| Post | Path |
|---|---|
| The Partnership Between Administrative and Synthetic Data | `/data/the-partnership-between-administrative-and-synthetic-data/` |
| Embracing a Cloud-Native Mindset in Federal Agencies | `/cloud-native/embracing-a-cloud-native-mindset-in-federal-agencies/` |
| Achieving Excellence: Passing ISO Surveillance Audit | `/news/achieving-excellence-passing-iso-surveillance-audit/` |
| Vidoori Resumes Work on $173M Contract Award | `/news/vidoori-resumes-work-on-173m-contract-award-for-enterprise-testing-support-services/` |
| Proud Supporter of the D.C. Heart Ball | `/news/vidoori-proudly-supports-the-american-heart-association-and-cpr-awareness/` |
| The Value of High Performance Testing | `/test-integration/the-importance-of-performance-testing/` |
| The Basics and Benefits of Test Data Management | `/cybersecurity/basics-of-test-data-management/` |
| Annual Event Recognizes Team and Community | `/news/vidooris-annual-party-recognizes-team-and-community/` |
| Vidoori Awarded $7.3M Contract to Modernize USCB CMMU System for 2030 | `/news/vidoori-awarded-7-3m-contract-to-modernize-u-s-census-bureaus-cmmu-system-for-2030/` |
| Vidoori Awarded 8(a) STARS III Contract | `/news/vidoori-awarded-contract-gsa-stars-iii/` |
| Vidoori Awarded Contract with NAVSUP | `/news/navsup-contract-awarded/` |
| Launch of Digital Dreamers Initiative | `/news/launch-of-digital-dreamers-initiative/` |
| Vidoori Joins Team Selected for New Contract (USCB Database CoE) | `/news/vidoori-joins-team-selected-to-establish-database-center-of-excellence-for-the-u-s-census-bureau/` |
| Killware is the Next Big Cyber Security Threat | `/news/killware-is-the-next-big-cyber-security-threat/` |
| Vidoori Opens New Maryland Headquarters | `/news/vidoori-opens-new-headquarters-in-new-carrolton-md/` |
| Largest Cybersecurity Companies List for 2021 | `/news/largest-cybersecurity-company-list/` |
| The Role of Synthetic Data in Software Development | `/test-integration/the-role-of-synthetic-data-in-software-development/` |
| How Cloud-Native Can Benefit Federal IT Systems | `/innovations/how-cloud-native-can-benefit-federal-it-systems/` |

### Contact form fields (`_src/pages/contact.html` → `functions/api/contact.js`)
| Field name | Label | Required |
|---|---|---|
| `firstName` | First name | yes |
| `lastName` | Last name | yes |
| `email` | Email address | yes |
| `phone` | Phone number | no |
| `company` | Company or organization | yes |
| `region` | Country or region | yes |
| `mediaInquiry` | Is this a media inquiry? | no |
| `message` | How can we help you? | yes |
| `privacyConsent` | Privacy Policy consent | yes |

`website` (honeypot) and `started_at` (timing check) are hidden anti-spam fields, not user input.
Turnstile guards submission — see [contact-form.md](contact-form.md).

### Media assets
- `assets/img/` — logos only, copied from `logos/`. No photography; diagrams are inline SVG.
- `assets/docs/` — one PDF: `Vidoori_CapabilityStatement.pdf` (110 KiB).
- No video. No `wp-content/` assets were carried over.

---

## Appendix: legacy capture (2026-08-28)

Snapshot of the legacy WordPress site, taken from `wp-sitemap.xml` before the static rebuild.
Raw HTML + extracted text were mirrored to a scratch dir during capture; this is the durable
record. **Do not edit this section to match the current site** — it exists to justify the rules
in `_redirects`, and rewriting it would strand those rules with no explanation.

Legacy size: 35 pages, 19 posts.

### Primary nav (legacy)
- **Who We Are** — `/who-we-are/`
  - Corporate Culture, Certifications, Awards & Recognition, Federal Government Contract Vehicles
- **What We Do** — `/what-we-do/`
  - Integration & Test, Cloud-Native, DevSecOps, Data Management
- **Insights** — `/insights/`
- **Careers** — `/careers/`
- **Contact** — `/contact/`

### Orphaned pages (existed, not linked from legacy nav)
- 10 leadership bios under `/who-we-are/leadership/*` — never linked from any page
- 4 extra service pages: `software-development`, `cybersecurity`, `applied-intelligence`, `strategy-consulting`
- `/pims/` — Portfolio and Investment Management System product page
- `/who-we-are/our-values/` — linked from body copy but not nav
- `/referral-program-form/`, `/referral-form-non-vpn-test/`, `/blog-2/`, `/tamela/` (cruft)

### What the legacy site had that the current one does not
| Legacy content | Disposition |
|---|---|
| `/pims/` product page | Not a real product. Removed; `/pims` → `/what-we-do/` |
| 8 more leadership bios (Heath, Odom, George, Stiers) + Board of Advisors (Adamo, Zimmerman, Harrigan) | Removed; all bio URLs → `/who-we-are/leadership/` |
| Intelligence: Facial recognition + Drone intelligence solution areas | Removed from `/what-we-do/applied-intelligence/` |
| 11 capability PDFs (per-practice, GSA I-FSS-600, referral T&Cs) | Deleted; only the corporate capability statement remains. Their `/wp-content/uploads/...` URLs now 404 |
| "2020 Security Cyber and Data Breach Statistics" post | Image-only, no body text — not ported. → `/insights/` |
| Hero video `Vidoori-Home-Hero-4.mp4`, ~103 `wp-content/` images | Not carried over; replaced by inline SVG |
| Contact Form 7 + reCAPTCHA | Replaced by a Pages Function with Turnstile + Postmark |

### Legacy contact form fields (Contact Form 7 + reCAPTCHA)
| Legacy name | Label / placeholder | Required |
|---|---|---|
| `your-name` | First Name | yes |
| `your-lastname` | Last Name | yes |
| `your-email` | E-mail Address | yes |
| `your-phone` | Phone Number (include country code) | no |
| `text-company` | Company/Organization | yes |
| `menu-region` | Country/Region (US, Canada, Mexico, South America, Europe, Asia, Africa, Australia) | yes |
| `checkbox-media-inquiry[]` | Is this a media inquiry? | no |
| `your-message` | How can we help you? (5000 char limit) | yes |
| `acceptance-privacy` | Privacy Policy consent | yes |

Intro copy: "Thank you for your interest in Vidoori. Please provide the requested information about
your inquiry so that we may route your request to the appropriate individual. You should receive a
response within three business days."
