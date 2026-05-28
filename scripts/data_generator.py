"""
Oracle Fusion AR – Random Test Data Generator
=============================================
Generates realistic, referentially-consistent CSV data for the full
Oracle AR table set found in this package.

Usage
-----
    python generate_oracle_ar_data.py [--invoices N] [--receipts N] [--customers N] [--out-dir ./output]

Defaults: 20 customers, 50 invoices, 15 receipts.

Load the produced CSVs in the order listed in LOAD_ORDER.txt.
"""

import argparse
import csv
import os
import random
import math
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducible randomness (override with --seed)
# ---------------------------------------------------------------------------
SEED = 42

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")


FAR_FUTURE = "4712-12-31"
AS_OF_DATE = date(2026, 2, 25)   # matches the suggested report parameter


# ---------------------------------------------------------------------------
# Static / reference pools (mimic real Oracle Fusion structures)
# ---------------------------------------------------------------------------

CURRENCIES = ["USD", "EUR", "GBP", "INR", "SGD", "AUD"]

COMPANY_SUFFIXES = [
    "Corporation", "LLC", "Ltd", "Inc", "Group", "Holdings",
    "Enterprises", "Partners", "Solutions", "Technologies", "Services",
]
COMPANY_PREFIXES = [
    "Acme", "Global", "Premier", "Pacific", "Atlantic", "Summit",
    "Pinnacle", "Apex", "Nexus", "Vertex", "Horizon", "Zenith",
    "Cascade", "Delta", "Alpha", "Omega", "Sigma", "Nova",
    "Vanguard", "Meridian", "Sterling", "Core", "Allied", "Metro",
    "Crown", "Keystone", "Frontier", "Bridge", "Heritage", "Legacy",
    "Dynamic", "Strategic", "Integrated", "Advanced", "Precision",
]

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank",
    "Irene", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Pete",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zoe",
]
LAST_NAMES = [
    "Smith", "Jones", "Brown", "Taylor", "Wilson", "Davis", "Clark",
    "Moore", "Thomas", "Jackson", "White", "Harris", "Martin", "Lewis",
    "Walker", "Hall", "Young", "Allen", "Wright", "King",
]


def random_person():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_company(used: set) -> str:
    for _ in range(200):
        name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
        if name not in used:
            used.add(name)
            return name
    return f"Company {len(used) + 1}"


# ---------------------------------------------------------------------------
# ID counters (start away from sample-data ranges so they don't collide)
# ---------------------------------------------------------------------------

class IDGen:
    def __init__(self, start: int):
        self._n = start

    def next(self) -> int:
        v = self._n
        self._n += 1
        return v


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate(
    num_customers: int,
    num_invoices: int,
    num_receipts: int,
    out_dir: Path,
):
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- ID generators --------------------------------------------------
    g_ledger         = IDGen(1000)
    g_bu             = IDGen(2000)
    g_le             = IDGen(3000)
    g_fvset          = IDGen(5000)
    g_fv             = IDGen(7000)
    g_org            = IDGen(8000)
    g_party          = IDGen(20000)
    g_acct           = IDGen(30000)
    g_party_site     = IDGen(40000)
    g_acct_site      = IDGen(50000)
    g_site_use       = IDGen(60000)
    g_prof_class     = IDGen(70000)
    g_profile        = IDGen(80000)
    g_batch_src      = IDGen(90000)
    g_trx_type       = IDGen(95000)
    g_cc             = IDGen(200000)
    g_okc            = IDGen(300000)
    g_trx            = IDGen(400000)
    g_trx_line       = IDGen(500000)
    g_gl_dist        = IDGen(600000)
    g_pay_sched      = IDGen(700000)
    g_app            = IDGen(800000)
    g_adj            = IDGen(900000)
    g_xla_hdr        = IDGen(1000000)
    g_event          = IDGen(1100000)

    used_company_names: set = set()

    # ======================================================================
    # 1. GL_LEDGERS
    # ======================================================================
    ledgers = []
    ledger_rows = []
    for currency in random.sample(CURRENCIES, min(3, len(CURRENCIES))):
        lid = g_ledger.next()
        name = f"{currency} Primary Ledger"
        ledgers.append({"LEDGER_ID": lid, "NAME": name, "CURRENCY_CODE": currency})
        ledger_rows.append({"LEDGER_ID": lid, "NAME": name, "CURRENCY_CODE": currency})

    write_csv(out_dir / "GL_LEDGERS.csv", ledger_rows,
              ["LEDGER_ID", "NAME", "CURRENCY_CODE"])

    # ======================================================================
    # 2. FUN_ALL_BUSINESS_UNITS_V
    # ======================================================================
    bus_units = []
    bu_rows = []
    for led in ledgers:
        bu_id = g_bu.next()
        bu_name = f"{led['CURRENCY_CODE']} Consulting BU"
        bus_units.append({"BU_ID": bu_id, "BU_NAME": bu_name,
                           "PRIMARY_LEDGER_ID": led["LEDGER_ID"],
                           "CURRENCY_CODE": led["CURRENCY_CODE"]})
        bu_rows.append({"BU_ID": bu_id, "BU_NAME": bu_name,
                         "PRIMARY_LEDGER_ID": led["LEDGER_ID"]})

    write_csv(out_dir / "FUN_ALL_BUSINESS_UNITS_V.csv", bu_rows,
              ["BU_ID", "BU_NAME", "PRIMARY_LEDGER_ID"])

    # ======================================================================
    # 3. XLE_ENTITY_PROFILES  (one legal entity per BU)
    # ======================================================================
    legal_entities = []
    le_rows = []
    for bu in bus_units:
        le_id = g_le.next()
        le_name = f"Legal Entity {bu['CURRENCY_CODE']}"
        legal_entities.append({"LEGAL_ENTITY_ID": le_id, "NAME": le_name,
                                 "BU_ID": bu["BU_ID"], "CURRENCY_CODE": bu["CURRENCY_CODE"]})
        le_rows.append({"LEGAL_ENTITY_ID": le_id, "NAME": le_name})

    write_csv(out_dir / "XLE_ENTITY_PROFILES.csv", le_rows,
              ["LEGAL_ENTITY_ID", "NAME"])

    # ======================================================================
    # 4. FND_ID_FLEX_SEGMENTS
    # ======================================================================
    fvset_le_id = g_fvset.next()
    fvset_loc_id = g_fvset.next()
    fvset_dept_id = g_fvset.next()

    flex_seg_rows = [
        {"FLEX_VALUE_SET_ID": fvset_le_id,   "SEGMENT_NAME": "Legal Entity", "ID_FLEX_CODE": "GL#"},
        {"FLEX_VALUE_SET_ID": fvset_loc_id,  "SEGMENT_NAME": "Location",     "ID_FLEX_CODE": "GL#"},
        {"FLEX_VALUE_SET_ID": fvset_dept_id, "SEGMENT_NAME": "Department",   "ID_FLEX_CODE": "GL#"},
    ]
    write_csv(out_dir / "FND_ID_FLEX_SEGMENTS.csv", flex_seg_rows,
              ["FLEX_VALUE_SET_ID", "SEGMENT_NAME", "ID_FLEX_CODE"])

    # ======================================================================
    # 5 & 6. FND_FLEX_VALUES / FND_FLEX_VALUES_TL
    # ======================================================================
    LOCATIONS  = ["L100", "L200", "L300", "L400", "L500"]
    DEPARTMENTS = ["D100", "D200", "D300", "D400", "D500"]

    fv_rows, fvtl_rows = [], []

    # Legal-entity flex values
    le_flex_map = {}   # legal_entity_id -> flex_value_id
    for le in legal_entities:
        fv_id = g_fv.next()
        fv_val = str(le["LEGAL_ENTITY_ID"] % 1000)
        le_flex_map[le["LEGAL_ENTITY_ID"]] = fv_id
        fv_rows.append({"FLEX_VALUE_ID": fv_id,
                         "FLEX_VALUE_SET_ID": fvset_le_id,
                         "FLEX_VALUE": fv_val})
        fvtl_rows.append({"FLEX_VALUE_ID": fv_id, "LANGUAGE": "US",
                           "DESCRIPTION": le["NAME"]})

    # Location flex values
    loc_fv_map = {}
    for loc in LOCATIONS:
        fv_id = g_fv.next()
        loc_fv_map[loc] = fv_id
        fv_rows.append({"FLEX_VALUE_ID": fv_id,
                         "FLEX_VALUE_SET_ID": fvset_loc_id,
                         "FLEX_VALUE": loc})
        fvtl_rows.append({"FLEX_VALUE_ID": fv_id, "LANGUAGE": "US",
                           "DESCRIPTION": f"Location {loc}"})

    # Department flex values
    dept_fv_map = {}
    for dept in DEPARTMENTS:
        fv_id = g_fv.next()
        dept_fv_map[dept] = fv_id
        fv_rows.append({"FLEX_VALUE_ID": fv_id,
                         "FLEX_VALUE_SET_ID": fvset_dept_id,
                         "FLEX_VALUE": dept})
        fvtl_rows.append({"FLEX_VALUE_ID": fv_id, "LANGUAGE": "US",
                           "DESCRIPTION": f"Department {dept}"})

    write_csv(out_dir / "FND_FLEX_VALUES.csv", fv_rows,
              ["FLEX_VALUE_ID", "FLEX_VALUE_SET_ID", "FLEX_VALUE"])
    write_csv(out_dir / "FND_FLEX_VALUES_TL.csv", fvtl_rows,
              ["FLEX_VALUE_ID", "LANGUAGE", "DESCRIPTION"])

    # ======================================================================
    # 7. HR_ORGANIZATION_UNITS  (one per BU)
    # ======================================================================
    org_units = []
    org_rows = []
    for bu in bus_units:
        oid = g_org.next()
        loc = random.choice(LOCATIONS)
        dept = random.choice(DEPARTMENTS)
        org_units.append({"ORGANIZATION_ID": oid, "NAME": f"{bu['BU_NAME']} Org",
                           "BU_ID": bu["BU_ID"], "ATTRIBUTE3": loc, "ATTRIBUTE4": dept})
        org_rows.append({"ORGANIZATION_ID": oid, "NAME": f"{bu['BU_NAME']} Org",
                          "ATTRIBUTE3": loc, "ATTRIBUTE4": dept})

    write_csv(out_dir / "HR_ORGANIZATION_UNITS.csv", org_rows,
              ["ORGANIZATION_ID", "NAME", "ATTRIBUTE3", "ATTRIBUTE4"])

    # ======================================================================
    # 8. OKC_K_HEADERS_ALL_B  (contracts – generated alongside transactions later)
    # We'll build these during invoice generation; declare the list now.
    # ======================================================================
    contracts = []   # filled during invoice loop

    # ======================================================================
    # 9–13. HZ_PARTIES / HZ_CUST_ACCOUNTS / HZ_PARTY_SITES /
    #        HZ_CUST_ACCT_SITES_ALL / HZ_CUST_SITE_USES_ALL
    # ======================================================================
    parties, party_rows       = [], []
    accounts, acct_rows       = [], []
    party_sites, ps_rows      = [], []
    acct_sites, as_rows       = [], []
    site_uses, su_rows        = [], []

    ACCOUNT_TYPES = {"A": "Active", "B": "Blocked", "C": "Collections"}

    for _ in range(num_customers):
        company = random_company(used_company_names)

        # Party
        pid = g_party.next()
        parties.append({"PARTY_ID": pid, "PARTY_NAME": company})
        party_rows.append({"PARTY_ID": pid, "PARTY_NAME": company})

        # Cust account
        caid = g_acct.next()
        acct_num = f"CUST-{caid % 100000:05d}"
        attr22 = random.choice(list(ACCOUNT_TYPES.keys()))
        accounts.append({"CUST_ACCOUNT_ID": caid, "PARTY_ID": pid,
                          "ACCOUNT_NAME": company, "ACCOUNT_NUMBER": acct_num,
                          "ATTRIBUTE22": attr22, "STATUS": "A"})
        acct_rows.append({"CUST_ACCOUNT_ID": caid, "PARTY_ID": pid,
                           "ACCOUNT_NAME": company, "ACCOUNT_NUMBER": acct_num,
                           "ATTRIBUTE22": attr22, "STATUS": "A"})

        # Party site (billing address)
        psid = g_party_site.next()
        site_num = f"SITE-{caid % 100000:05d}-BILL"
        party_sites.append({"PARTY_SITE_ID": psid, "PARTY_ID": pid,
                              "SITE_NUMBER": site_num})
        ps_rows.append({"PARTY_SITE_ID": psid, "PARTY_ID": pid,
                         "SITE_NUMBER": site_num})

        # Cust acct site
        asid = g_acct_site.next()
        acct_sites.append({"CUST_ACCT_SITE_ID": asid, "CUST_ACCOUNT_ID": caid,
                             "BILL_TO_FLAG": "P", "STATUS": "A",
                             "PARTY_SITE_ID": psid})
        as_rows.append({"CUST_ACCT_SITE_ID": asid, "CUST_ACCOUNT_ID": caid,
                         "BILL_TO_FLAG": "P", "STATUS": "A",
                         "PARTY_SITE_ID": psid})

        # Site use
        suid = g_site_use.next()
        site_uses.append({"SITE_USE_ID": suid, "CUST_ACCT_SITE_ID": asid,
                           "SITE_USE_CODE": "BILL_TO", "STATUS": "A",
                           "CUST_ACCOUNT_ID": caid})
        su_rows.append({"SITE_USE_ID": suid, "CUST_ACCT_SITE_ID": asid,
                         "SITE_USE_CODE": "BILL_TO", "STATUS": "A"})

    write_csv(out_dir / "HZ_PARTIES.csv",           party_rows, ["PARTY_ID", "PARTY_NAME"])
    write_csv(out_dir / "HZ_CUST_ACCOUNTS.csv",     acct_rows,
              ["CUST_ACCOUNT_ID", "PARTY_ID", "ACCOUNT_NAME", "ACCOUNT_NUMBER", "ATTRIBUTE22", "STATUS"])
    write_csv(out_dir / "HZ_PARTY_SITES.csv",       ps_rows,
              ["PARTY_SITE_ID", "PARTY_ID", "SITE_NUMBER"])
    write_csv(out_dir / "HZ_CUST_ACCT_SITES_ALL.csv", as_rows,
              ["CUST_ACCT_SITE_ID", "CUST_ACCOUNT_ID", "BILL_TO_FLAG", "STATUS", "PARTY_SITE_ID"])
    write_csv(out_dir / "HZ_CUST_SITE_USES_ALL.csv", su_rows,
              ["SITE_USE_ID", "CUST_ACCT_SITE_ID", "SITE_USE_CODE", "STATUS"])

    # ======================================================================
    # 14–15. HZ_CUST_PROFILE_CLASSES / HZ_CUSTOMER_PROFILES_F
    # ======================================================================
    PROFILE_CLASS_DEFS = [
        ("Standard Customer", 95),
        ("High Risk Customer", 50),
        ("Premium Customer", 99),
        ("New Customer", 80),
        ("Government Account", 100),
    ]
    prof_classes = []
    pc_rows = []
    for name, pct in PROFILE_CLASS_DEFS:
        pcid = g_prof_class.next()
        prof_classes.append({"PROFILE_CLASS_ID": pcid, "NAME": name,
                               "PERCENT_COLLECTABLE": pct})
        pc_rows.append({"PROFILE_CLASS_ID": pcid, "NAME": name})

    write_csv(out_dir / "HZ_CUST_PROFILE_CLASSES.csv", pc_rows,
              ["PROFILE_CLASS_ID", "NAME"])

    ACCOUNT_STATUSES = ["Current", "Collections", "Watch", "Closed"]
    prof_rows = []
    # Attach a profile to every cust account
    acct_profile_map = {}   # cust_account_id -> profile class
    for acct in accounts:
        pc = random.choice(prof_classes)
        pf_id = g_profile.next()
        eff_start = rand_date(date(2018, 1, 1), date(2022, 12, 31))
        status = random.choice(ACCOUNT_STATUSES)
        acct_profile_map[acct["CUST_ACCOUNT_ID"]] = pc
        prof_rows.append({
            "PROFILE_ID": pf_id,
            "CUST_ACCOUNT_ID": acct["CUST_ACCOUNT_ID"],
            "PROFILE_CLASS_ID": pc["PROFILE_CLASS_ID"],
            "EFFECTIVE_START_DATE": fmt(eff_start),
            "EFFECTIVE_END_DATE": FAR_FUTURE,
            "PERCENT_COLLECTABLE": pc["PERCENT_COLLECTABLE"],
            "ACCOUNT_STATUS": status,
        })

    write_csv(out_dir / "HZ_CUSTOMER_PROFILES_F.csv", prof_rows,
              ["PROFILE_ID", "CUST_ACCOUNT_ID", "PROFILE_CLASS_ID",
               "EFFECTIVE_START_DATE", "EFFECTIVE_END_DATE",
               "PERCENT_COLLECTABLE", "ACCOUNT_STATUS"])

    # ======================================================================
    # 16. RA_BATCH_SOURCES_ALL
    # ======================================================================
    batch_sources = []
    bs_rows = []
    for src_name in ["Contract Invoices", "Manual", "EDI Import", "Web Portal"]:
        bid = g_batch_src.next()
        batch_sources.append({"BATCH_SOURCE_SEQ_ID": bid, "NAME": src_name})
        bs_rows.append({"BATCH_SOURCE_SEQ_ID": bid, "NAME": src_name})

    write_csv(out_dir / "RA_BATCH_SOURCES_ALL.csv", bs_rows,
              ["BATCH_SOURCE_SEQ_ID", "NAME"])

    # ======================================================================
    # 17. RA_CUST_TRX_TYPES_ALL
    # ======================================================================
    TRX_TYPE_DEFS = [
        ("INV", "Standard Invoice"),
        ("CM",  "Credit Memo"),
        ("DM",  "Debit Memo"),
    ]
    trx_types = []
    tt_rows = []
    for ttype, tname in TRX_TYPE_DEFS:
        ttid = g_trx_type.next()
        trx_types.append({"CUST_TRX_TYPE_SEQ_ID": ttid, "TYPE": ttype, "NAME": tname})
        tt_rows.append({"CUST_TRX_TYPE_SEQ_ID": ttid, "TYPE": ttype, "NAME": tname})

    write_csv(out_dir / "RA_CUST_TRX_TYPES_ALL.csv", tt_rows,
              ["CUST_TRX_TYPE_SEQ_ID", "TYPE", "NAME"])

    # ======================================================================
    # 18. GL_CODE_COMBINATIONS
    # ======================================================================
    ACCOUNT_CODES = ["4000", "4100", "4200", "4300", "5000", "5100", "1200", "1300"]
    cc_list = []
    cc_rows = []
    for le in legal_entities:
        for loc in random.sample(LOCATIONS, 3):
            for dept in random.sample(DEPARTMENTS, 2):
                for accode in random.sample(ACCOUNT_CODES, 3):
                    ccid = g_cc.next()
                    seg1 = str(le["LEGAL_ENTITY_ID"] % 1000)
                    desc = f"Acct {accode} - {loc} - {dept}"
                    cc_list.append({
                        "CODE_COMBINATION_ID": ccid,
                        "SEGMENT1": seg1, "SEGMENT2": dept,
                        "SEGMENT3": loc,  "SEGMENT4": accode,
                        "DESCRIPTION": desc,
                        "LEGAL_ENTITY_ID": le["LEGAL_ENTITY_ID"],
                    })
                    cc_rows.append({
                        "CODE_COMBINATION_ID": ccid,
                        "SEGMENT1": seg1, "SEGMENT2": dept,
                        "SEGMENT3": loc,  "SEGMENT4": accode,
                        "DESCRIPTION": desc,
                    })

    write_csv(out_dir / "GL_CODE_COMBINATIONS.csv", cc_rows,
              ["CODE_COMBINATION_ID", "SEGMENT1", "SEGMENT2", "SEGMENT3",
               "SEGMENT4", "DESCRIPTION"])

    # ======================================================================
    # 19. RA_CUSTOMER_TRX_ALL  (invoices + credit memos)
    # 20. RA_CUSTOMER_TRX_LINES_ALL
    # 21. RA_CUST_TRX_LINE_GL_DIST_ALL
    # 22. AR_PAYMENT_SCHEDULES_ALL
    # 23. AR_RECEIVABLE_APPLICATIONS_ALL   (cash receipts — receipt rows)
    # 24. AR_ADJUSTMENTS_ALL
    # 8.  OKC_K_HEADERS_ALL_B
    # XLA tables
    # ======================================================================
    trx_rows, trx_line_rows, gl_dist_rows = [], [], []
    pay_sched_rows = []
    xla_hdr_rows, xla_line_rows, xla_dist_rows = [], [], []
    okc_rows = []
    adj_rows = []

    # AR roles for invoice line attributes
    def role_label(role_code, role_name, person_name):
        return f"{role_code}-{g_trx.next() % 900000 + 100000}-{person_name} {role_name}"

    ROLE_CODES = {"Contract Authority": "CA", "Billing Manager": "BM",
                  "Billing Authority": "BA", "Project Manager": "PM"}

    INV_TYPE = next(t for t in trx_types if t["TYPE"] == "INV")
    CM_TYPE  = next(t for t in trx_types if t["TYPE"] == "CM")

    # We need an incrementing invoice number counter separate from ID
    inv_counter = [10001]

    def next_inv_num(prefix="INV"):
        n = inv_counter[0]
        inv_counter[0] += 1
        return f"{prefix}-{n}"

    rcp_counter = [90001]

    def next_rcp_num():
        n = rcp_counter[0]
        rcp_counter[0] += 1
        return f"RCP-{n}"

    # Build contracts pool
    num_contracts = max(5, num_invoices // 4)
    contract_pool = []
    for i in range(num_contracts):
        oid = g_okc.next()
        le = random.choice(legal_entities)
        org = next(o for o in org_units if o["BU_ID"] == le["BU_ID"])
        con_num = f"CON-{oid % 100000}"
        contract_pool.append({
            "ID": oid, "CONTRACT_NUMBER": con_num,
            "LEGAL_ENTITY_ID": le["LEGAL_ENTITY_ID"],
            "OWNING_ORG_ID": org["ORGANIZATION_ID"],
            "VERSION_TYPE": random.choice(["C", "A"]),
        })
        okc_rows.append({
            "ID": oid, "CONTRACT_NUMBER": con_num,
            "LEGAL_ENTITY_ID": le["LEGAL_ENTITY_ID"],
            "OWNING_ORG_ID": org["ORGANIZATION_ID"],
            "VERSION_TYPE": contract_pool[-1]["VERSION_TYPE"],
        })

    write_csv(out_dir / "OKC_K_HEADERS_ALL_B.csv", okc_rows,
              ["ID", "CONTRACT_NUMBER", "LEGAL_ENTITY_ID", "OWNING_ORG_ID", "VERSION_TYPE"])
    write_csv(out_dir / "OKC_K_HEADERS_B.csv", okc_rows,
              ["ID", "CONTRACT_NUMBER", "LEGAL_ENTITY_ID", "OWNING_ORG_ID", "VERSION_TYPE"])

    # Track all invoice payment schedules for receipt application
    open_inv_schedules = []   # list of pay-sched dicts for open invoices

    for _ in range(num_invoices):
        acct = random.choice(accounts)
        caid = acct["CUST_ACCOUNT_ID"]

        # Resolve linked entities
        su = next(s for s in site_uses if s["CUST_ACCOUNT_ID"] == caid)
        bu = random.choice(bus_units)
        le = next(l for l in legal_entities if l["BU_ID"] == bu["BU_ID"])
        org = next(o for o in org_units if o["BU_ID"] == bu["BU_ID"])
        cc = random.choice([c for c in cc_list
                             if c["LEGAL_ENTITY_ID"] == le["LEGAL_ENTITY_ID"]])
        batch_src = random.choice(batch_sources)
        contract = random.choice(contract_pool)

        # Dates: invoice anywhere in the last 150 days before AS_OF_DATE
        trx_date = rand_date(AS_OF_DATE - timedelta(days=150), AS_OF_DATE - timedelta(days=1))
        gl_date = trx_date

        trx_id = g_trx.next()
        trx_num = next_inv_num()
        amount = round(random.uniform(500, 50000), 2)
        tax = round(amount * random.uniform(0.05, 0.18), 2)
        total = round(amount + tax, 2)

        # RA_CUSTOMER_TRX_ALL
        trx_rows.append({
            "CUSTOMER_TRX_ID": trx_id,
            "LEGAL_ENTITY_ID": le["LEGAL_ENTITY_ID"],
            "TRX_DATE": fmt(trx_date),
            "TRX_NUMBER": trx_num,
            "BILL_TO_CUSTOMER_ID": caid,
            "BATCH_SOURCE_SEQ_ID": batch_src["BATCH_SOURCE_SEQ_ID"],
            "ORG_ID": bu["BU_ID"],
        })

        # RA_CUSTOMER_TRX_LINES_ALL
        line_id = g_trx_line.next()
        ca_person = random_person()
        bm_person = random_person()
        ba_person = random_person()

        trx_line_rows.append({
            "CUSTOMER_TRX_LINE_ID": line_id,
            "CUSTOMER_TRX_ID": trx_id,
            "LINE_TYPE": "LINE",
            "LINE_NUMBER": 1,
            "ATTRIBUTE1": contract["CONTRACT_NUMBER"],
            "ATTRIBUTE3": f"CA-{contract['ID'] % 100000}-{ca_person} Contract Authority",
            "ATTRIBUTE4": f"BM-{contract['ID'] % 100000}-{bm_person} Billing Manager",
            "ATTRIBUTE5": f"BA-{contract['ID'] % 100000}-{ba_person} Billing Authority",
            "ATTRIBUTE6": org["NAME"],
            "TAX_RECOVERABLE": tax,
            "EXTENDED_AMOUNT": amount,
        })

        # RA_CUST_TRX_LINE_GL_DIST_ALL
        event_id = g_event.next()
        dist_id = g_gl_dist.next()
        xla_hdr_id = g_xla_hdr.next()

        gl_dist_rows.append({
            "CUST_TRX_LINE_GL_DIST_ID": dist_id,
            "CUSTOMER_TRX_ID": trx_id,
            "CUSTOMER_TRX_LINE_ID": line_id,
            "CODE_COMBINATION_ID": cc["CODE_COMBINATION_ID"],
            "ACCOUNT_CLASS": "REC",
            "GL_POSTED_DATE": fmt(gl_date),
            "EVENT_ID": event_id,
        })

        # XLA
        xla_hdr_rows.append({"AE_HEADER_ID": xla_hdr_id, "EVENT_ID": event_id})
        xla_line_rows.append({
            "AE_HEADER_ID": xla_hdr_id,
            "CODE_COMBINATION_ID": cc["CODE_COMBINATION_ID"],
            "ACCOUNTING_CLASS_CODE": "REVENUE",
        })
        xla_dist_rows.append({
            "SOURCE_DISTRIBUTION_ID_NUM_1": dist_id,
            "SOURCE_DISTRIBUTION_TYPE": "RA_CUST_TRX_LINE_GL_DIST_ALL",
            "AE_HEADER_ID": xla_hdr_id,
        })

        # AR_PAYMENT_SCHEDULES_ALL
        # Simulate various aging buckets
        days_old = (AS_OF_DATE - trx_date).days
        paid_partial = random.random() < 0.25
        discount = 0
        if paid_partial:
            partial_pct = random.uniform(0.1, 0.7)
            remaining = round(total * (1 - partial_pct), 2)
            discount = round(total * random.uniform(0, 0.02), 2)
        else:
            remaining = total

        status = "CL" if remaining <= 0 else "OP"
        closed_date = FAR_FUTURE if status == "OP" else fmt(rand_date(trx_date, AS_OF_DATE))

        ps_id = g_pay_sched.next()
        pay_sched_rows.append({
            "PAYMENT_SCHEDULE_ID": ps_id,
            "CUSTOMER_TRX_ID": trx_id,
            "ORG_ID": bu["BU_ID"],
            "CUSTOMER_ID": caid,
            "CUSTOMER_SITE_USE_ID": su["SITE_USE_ID"],
            "CUST_TRX_TYPE_SEQ_ID": INV_TYPE["CUST_TRX_TYPE_SEQ_ID"],
            "TRX_DATE": fmt(trx_date),
            "TRX_NUMBER": trx_num,
            "CLASS": "INV",
            "CASH_RECEIPT_ID": "",
            "AMOUNT_DUE_ORIGINAL": total,
            "DISCOUNT_TAKEN_EARNED": discount,
            "AMOUNT_DUE_REMAINING": remaining,
            "GL_DATE": fmt(gl_date),
            "GL_DATE_CLOSED": closed_date,
            "STATUS": status,
        })

        if status == "OP":
            open_inv_schedules.append({
                "PAYMENT_SCHEDULE_ID": ps_id,
                "AMOUNT_DUE_REMAINING": remaining,
                "ORG_ID": bu["BU_ID"],
                "CUSTOMER_ID": caid,
            })

        # AR_ADJUSTMENTS_ALL – ~15% of invoices get an adjustment
        if random.random() < 0.15:
            adj_date = rand_date(trx_date, AS_OF_DATE)
            adj_amount = -round(random.uniform(10, min(200, remaining * 0.3)), 2)
            adj_rows.append({
                "ADJUSTMENT_ID": g_adj.next(),
                "PAYMENT_SCHEDULE_ID": ps_id,
                "GL_DATE": fmt(adj_date),
                "STATUS": "A",
                "AMOUNT": adj_amount,
            })

    # ======================================================================
    # 23. AR_RECEIVABLE_APPLICATIONS_ALL  (cash receipts)
    # ======================================================================
    app_rows = []
    rcp_pay_sched_rows = []   # receipt-class rows in AR_PAYMENT_SCHEDULES_ALL

    for _ in range(num_receipts):
        apply_date = rand_date(AS_OF_DATE - timedelta(days=90), AS_OF_DATE)
        rcp_amount = round(random.uniform(200, 20000), 2)

        rcp_ps_id = g_pay_sched.next()
        rcp_num = next_rcp_num()
        rcp_type = random.choice(["UNAPP", "APP", "ACC"])   # unapplied / applied / on-account

        # Pick a customer to associate the receipt with
        acct = random.choice(accounts)
        caid = acct["CUST_ACCOUNT_ID"]
        su = next(s for s in site_uses if s["CUST_ACCOUNT_ID"] == caid)

        # Receipt payment schedule
        rcp_pay_sched_rows.append({
            "PAYMENT_SCHEDULE_ID": rcp_ps_id,
            "CUSTOMER_TRX_ID": "",
            "ORG_ID": random.choice(bus_units)["BU_ID"],
            "CUSTOMER_ID": caid,
            "CUSTOMER_SITE_USE_ID": su["SITE_USE_ID"],
            "CUST_TRX_TYPE_SEQ_ID": "",
            "TRX_DATE": fmt(apply_date),
            "TRX_NUMBER": rcp_num,
            "CLASS": "PMT",
            "CASH_RECEIPT_ID": rcp_ps_id,
            "AMOUNT_DUE_ORIGINAL": -rcp_amount,
            "DISCOUNT_TAKEN_EARNED": 0,
            "AMOUNT_DUE_REMAINING": 0 if rcp_type == "APP" else -rcp_amount,
            "GL_DATE": fmt(apply_date),
            "GL_DATE_CLOSED": fmt(apply_date) if rcp_type == "APP" else FAR_FUTURE,
            "STATUS": "CL" if rcp_type == "APP" else "OP",
        })

        app_id = g_app.next()

        if rcp_type == "APP" and open_inv_schedules:
            # Apply to a random open invoice
            target = random.choice(open_inv_schedules)
            apply_amt = min(rcp_amount, target["AMOUNT_DUE_REMAINING"])
            app_rows.append({
                "RECEIVABLE_APPLICATION_ID": app_id,
                "APPLIED_PAYMENT_SCHEDULE_ID": target["PAYMENT_SCHEDULE_ID"],
                "PAYMENT_SCHEDULE_ID": rcp_ps_id,
                "CASH_RECEIPT_ID": rcp_ps_id,
                "STATUS": "APP",
                "APPLY_DATE": fmt(apply_date),
                "APPLICATION_TYPE": "CASH",
                "AMOUNT_APPLIED": apply_amt,
            })
        elif rcp_type == "UNAPP":
            app_rows.append({
                "RECEIVABLE_APPLICATION_ID": app_id,
                "APPLIED_PAYMENT_SCHEDULE_ID": "",
                "PAYMENT_SCHEDULE_ID": rcp_ps_id,
                "CASH_RECEIPT_ID": rcp_ps_id,
                "STATUS": "UNAPP",
                "APPLY_DATE": fmt(apply_date),
                "APPLICATION_TYPE": "CASH",
                "AMOUNT_APPLIED": rcp_amount,
            })
        else:  # on-account
            app_rows.append({
                "RECEIVABLE_APPLICATION_ID": app_id,
                "APPLIED_PAYMENT_SCHEDULE_ID": "",
                "PAYMENT_SCHEDULE_ID": rcp_ps_id,
                "CASH_RECEIPT_ID": rcp_ps_id,
                "STATUS": "ACC",
                "APPLY_DATE": fmt(apply_date),
                "APPLICATION_TYPE": "CASH",
                "AMOUNT_APPLIED": rcp_amount,
            })

    # Merge invoice + receipt payment schedules
    all_pay_sched = pay_sched_rows + rcp_pay_sched_rows
    write_csv(out_dir / "AR_PAYMENT_SCHEDULES_ALL.csv", all_pay_sched,
              ["PAYMENT_SCHEDULE_ID", "CUSTOMER_TRX_ID", "ORG_ID", "CUSTOMER_ID",
               "CUSTOMER_SITE_USE_ID", "CUST_TRX_TYPE_SEQ_ID", "TRX_DATE", "TRX_NUMBER",
               "CLASS", "CASH_RECEIPT_ID", "AMOUNT_DUE_ORIGINAL", "DISCOUNT_TAKEN_EARNED",
               "AMOUNT_DUE_REMAINING", "GL_DATE", "GL_DATE_CLOSED", "STATUS"])

    write_csv(out_dir / "RA_CUSTOMER_TRX_ALL.csv", trx_rows,
              ["CUSTOMER_TRX_ID", "LEGAL_ENTITY_ID", "TRX_DATE", "TRX_NUMBER",
               "BILL_TO_CUSTOMER_ID", "BATCH_SOURCE_SEQ_ID", "ORG_ID"])

    write_csv(out_dir / "RA_CUSTOMER_TRX_LINES_ALL.csv", trx_line_rows,
              ["CUSTOMER_TRX_LINE_ID", "CUSTOMER_TRX_ID", "LINE_TYPE", "LINE_NUMBER",
               "ATTRIBUTE1", "ATTRIBUTE3", "ATTRIBUTE4", "ATTRIBUTE5", "ATTRIBUTE6",
               "TAX_RECOVERABLE", "EXTENDED_AMOUNT"])

    write_csv(out_dir / "RA_CUST_TRX_LINE_GL_DIST_ALL.csv", gl_dist_rows,
              ["CUST_TRX_LINE_GL_DIST_ID", "CUSTOMER_TRX_ID", "CUSTOMER_TRX_LINE_ID",
               "CODE_COMBINATION_ID", "ACCOUNT_CLASS", "GL_POSTED_DATE", "EVENT_ID"])

    write_csv(out_dir / "AR_RECEIVABLE_APPLICATIONS_ALL.csv", app_rows,
              ["RECEIVABLE_APPLICATION_ID", "APPLIED_PAYMENT_SCHEDULE_ID",
               "PAYMENT_SCHEDULE_ID", "CASH_RECEIPT_ID", "STATUS", "APPLY_DATE",
               "APPLICATION_TYPE", "AMOUNT_APPLIED"])

    write_csv(out_dir / "AR_ADJUSTMENTS_ALL.csv", adj_rows,
              ["ADJUSTMENT_ID", "PAYMENT_SCHEDULE_ID", "GL_DATE", "STATUS", "AMOUNT"])

    # XLA tables
    write_csv(out_dir / "XLA_AE_HEADERS.csv",       xla_hdr_rows,  ["AE_HEADER_ID", "EVENT_ID"])
    write_csv(out_dir / "XLA_AE_LINES.csv",          xla_line_rows,
              ["AE_HEADER_ID", "CODE_COMBINATION_ID", "ACCOUNTING_CLASS_CODE"])
    write_csv(out_dir / "XLA_DISTRIBUTION_LINKS.csv", xla_dist_rows,
              ["SOURCE_DISTRIBUTION_ID_NUM_1", "SOURCE_DISTRIBUTION_TYPE", "AE_HEADER_ID"])

    # Summary
    counts = {
        "GL_LEDGERS":                    len(ledger_rows),
        "FUN_ALL_BUSINESS_UNITS_V":      len(bu_rows),
        "XLE_ENTITY_PROFILES":           len(le_rows),
        "FND_ID_FLEX_SEGMENTS":          len(flex_seg_rows),
        "FND_FLEX_VALUES":               len(fv_rows),
        "FND_FLEX_VALUES_TL":            len(fvtl_rows),
        "HR_ORGANIZATION_UNITS":         len(org_rows),
        "OKC_K_HEADERS_ALL_B":           len(okc_rows),
        "HZ_PARTIES":                    len(party_rows),
        "HZ_CUST_ACCOUNTS":              len(acct_rows),
        "HZ_PARTY_SITES":                len(ps_rows),
        "HZ_CUST_ACCT_SITES_ALL":        len(as_rows),
        "HZ_CUST_SITE_USES_ALL":         len(su_rows),
        "HZ_CUST_PROFILE_CLASSES":       len(pc_rows),
        "HZ_CUSTOMER_PROFILES_F":        len(prof_rows),
        "RA_BATCH_SOURCES_ALL":          len(bs_rows),
        "RA_CUST_TRX_TYPES_ALL":         len(tt_rows),
        "GL_CODE_COMBINATIONS":          len(cc_rows),
        "RA_CUSTOMER_TRX_ALL":           len(trx_rows),
        "RA_CUSTOMER_TRX_LINES_ALL":     len(trx_line_rows),
        "RA_CUST_TRX_LINE_GL_DIST_ALL":  len(gl_dist_rows),
        "AR_PAYMENT_SCHEDULES_ALL":      len(all_pay_sched),
        "AR_RECEIVABLE_APPLICATIONS_ALL":len(app_rows),
        "AR_ADJUSTMENTS_ALL":            len(adj_rows),
        "XLA_AE_HEADERS":                len(xla_hdr_rows),
        "XLA_AE_LINES":                  len(xla_line_rows),
        "XLA_DISTRIBUTION_LINKS":        len(xla_dist_rows),
    }
    return counts


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: list, fieldnames: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate Oracle AR Fusion test data CSVs."
    )
    parser.add_argument("--customers", type=int, default=20,
                        help="Number of customers to generate (default: 20)")
    parser.add_argument("--invoices",  type=int, default=50,
                        help="Number of invoices to generate (default: 50)")
    parser.add_argument("--receipts",  type=int, default=15,
                        help="Number of cash receipts to generate (default: 15)")
    parser.add_argument("--out-dir",   type=str, default="./generated_data",
                        help="Output directory (default: ./generated_data)")
    parser.add_argument("--seed",      type=int, default=SEED,
                        help=f"Random seed for reproducibility (default: {SEED})")
    args = parser.parse_args()

    random.seed(args.seed)

    out = Path(args.out_dir)
    print(f"\nGenerating Oracle AR test data → {out.resolve()}\n")

    counts = generate(
        num_customers=args.customers,
        num_invoices=args.invoices,
        num_receipts=args.receipts,
        out_dir=out,
    )

    max_name = max(len(k) for k in counts)
    print(f"{'Table':<{max_name}}  Rows")
    print("-" * (max_name + 8))
    for table, n in counts.items():
        print(f"{table:<{max_name}}  {n:>6,}")
    total = sum(counts.values())
    print("-" * (max_name + 8))
    print(f"{'TOTAL':<{max_name}}  {total:>6,}")
    print(f"\nDone. CSVs written to: {out.resolve()}")


if __name__ == "__main__":
    main()