import json

from conftest import to_hex

CLAIM = "claim-2026-11"
URL = "https://status.vendor.example.com/november"
REQUIRED = 9990  # 99.90%
DAYS = 30
TOTAL = DAYS * 1440  # 43200 minutes

BODY = (
    "November service report. Total availability window 43,200 minutes. "
    "Outage on 2026-11-07 lasted 86 minutes (database failover). "
    "All other days were available. Contact: ops@vendor.example.com."
)


def _mock(vm, body=BODY, finding=None):
    vm.mock_web(r".*status\.vendor\.example\.com/november.*", {"status": 200, "body": body})
    if finding is not None:
        vm.mock_llm(r".*SERVICE STATUS SCREEN.*", json.dumps(finding))


def _finding(downtime=0, consistency="consistent", summary="One outage window."):
    return {
        "downtime_minutes": downtime,
        "consistency": consistency,
        "summary": summary,
    }


def _claim(contract, vm, publisher, required=REQUIRED, days=DAYS):
    vm.sender = publisher
    contract.register_claim(CLAIM, "Vendor Inc", URL, required, days)


def test_met_sla_owes_no_credit(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=0))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["state"] == 1
    assert result["decision"] == 1
    assert result["uptime_bps"] == 10000
    assert result["credit_bps"] == 0
    assert contract.is_credit_owed(CLAIM) is False


def test_small_shortfall_pays_tier_one(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=86))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["uptime_bps"] == 9980
    assert result["decision"] == 2
    assert result["credit_bps"] == 1000
    assert contract.is_credit_owed(CLAIM) is True


def test_one_more_minute_crosses_into_tier_two(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=87))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["uptime_bps"] == 9979
    assert result["decision"] == 3
    assert result["credit_bps"] == 2500


def test_mid_shortfall_stays_in_tier_two(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=216))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["uptime_bps"] == 9950
    assert result["decision"] == 3
    assert result["credit_bps"] == 2500


def test_major_outage_pays_tier_three(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=600))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["decision"] == 4
    assert result["credit_bps"] == 5000
    assert result["downtime_minutes"] == 600


def test_unreadable_status_page_needs_review(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    direct_vm.mock_web(r".*status\.vendor\.example\.com.*", {"status": 500, "body": ""})

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["decision"] == 5
    assert result["credit_bps"] == 0
    assert result["consistency"] == "insufficient"


def test_conflicting_report_needs_review(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=120, consistency="conflicting"))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["decision"] == 5
    assert result["consistency"] == "conflicting"


def test_downtime_longer_than_period_needs_review(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    _mock(direct_vm, finding=_finding(downtime=TOTAL + 1))

    contract.assess(CLAIM)

    result = contract.get_claim(CLAIM)
    assert result["decision"] == 5
    assert result["credit_bps"] == 0


def test_fail_closed_leader_requires_the_sentinel(direct_deploy):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")

    assert contract._is_fail_closed(
        {"downtime_minutes": 10 ** 9, "consistency": "insufficient"}
    ) is True
    assert contract._is_fail_closed(
        {"downtime_minutes": 0, "consistency": "insufficient"}
    ) is False
    assert contract._is_fail_closed(
        {"downtime_minutes": 10 ** 9, "consistency": "consistent"}
    ) is False
    assert contract._is_fail_closed("garbage") is False


def test_duplicate_claim_is_rejected(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    try:
        contract.register_claim(CLAIM, "Other Vendor", URL, REQUIRED, DAYS)
        raised = False
    except Exception:
        raised = True
    assert raised is True


def test_invalid_period_is_rejected(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    direct_vm.sender = direct_alice
    try:
        contract.register_claim(CLAIM, "Vendor Inc", URL, REQUIRED, 0)
        raised = False
    except Exception:
        raised = True
    assert raised is True


def test_only_publisher_can_withdraw(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    _claim(contract, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    try:
        contract.withdraw(CLAIM)
        raised = False
    except Exception:
        raised = True
    assert raised is True


def test_policy_schedule_is_stable(direct_deploy):
    contract = direct_deploy("contracts/sla_credit_adjudicator.py")
    p = contract.policy()
    assert p["policy_version"] == "sla-credit-v1"
    assert p["bps"] == 10000
    assert p["tier_1_shortfall_bps"] == 10
    assert p["tier_2_shortfall_bps"] == 50
    assert p["tier_1_credit_bps"] == 1000
    assert p["tier_2_credit_bps"] == 2500
    assert p["tier_3_credit_bps"] == 5000
    assert p["no_credit"] == 1
    assert p["review_required"] == 5
