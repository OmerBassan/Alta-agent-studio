"""The Business Specification: schema, version pinning, validation suite, compiler.

Every validation check is proven by injecting the violation it guards against
into a valid specification and observing the blocking finding (FR96): a check
that has never been seen to fire is not evidence of anything."""

import pytest

from studio.spec import COMPILER_VERSION, SpecificationError, compile_specification, load_specification, validate
from studio.spec.model import EXPRESSION_AREAS, area_established

DENTAL = "dental"


def codes(report, severity="blocking"):
    return {f.code for f in report.findings if f.severity == severity}


# --- the business specification as written -------------------------------------

def test_dental_passes_the_gate_with_every_area_established(business_copy):
    loaded = load_specification(business_copy(DENTAL))
    report = validate(loaded)
    assert report.passed, [f.message for f in report.blocking]
    assert report.findings == ()
    assert all(area_established(loaded.spec, area) for area in EXPRESSION_AREAS)
    assert len(EXPRESSION_AREAS) == 17


# --- FR14: an unwritten area is a recorded absence, never a default ------------------

def test_missing_optional_area_is_reported_not_defaulted(business_copy):
    spec = business_copy(DENTAL, replace=[("[data_lifecycle]\nretention_days = 365\ndelete_on_request = true\n", "")])
    report = validate(load_specification(spec))
    ex17 = [f for f in report.findings if f.area == "EX17"]
    assert report.passed
    assert [f.severity for f in ex17] == ["warning"]
    assert "not established" in ex17[0].message


def test_missing_escalation_destination_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[('destination = "frontdesk@brightsmile.example"', 'destination = ""')])
    report = validate(load_specification(spec))
    assert not report.passed
    assert any(f.area == "EX10" and f.severity == "blocking" for f in report.findings)


def test_empty_disclosure_blocks(business_copy):
    old = "disclosure = \"You are writing to Bright Smile Dental's automated assistant. A member of our team reads anything it hands over.\""
    report = validate(load_specification(business_copy(DENTAL, replace=[(old, 'disclosure = " "')])))
    assert any(f.location == "identity.disclosure" for f in report.blocking)


# --- FR18 / FR24: ordering cannot be expressed ---------------------------------------

def test_an_ordering_key_is_rejected_with_a_reason(business_copy):
    spec = business_copy(DENTAL, replace=[('id = "book_visit"\n', 'id = "book_visit"\nsteps = ["ask name", "book"]\n')])
    with pytest.raises(SpecificationError) as exc:
        load_specification(spec)
    finding = exc.value.findings[0]
    assert finding.code == "sequencing_construct"
    assert "cannot express ordering" in finding.message


def test_ordering_in_prose_is_rejected(business_copy):
    spec = business_copy(DENTAL, replace=[
        ('description = "The patient wants to book an appointment."',
         'description = "First ask for the patient name, then check the calendar."')])
    report = validate(load_specification(spec))
    assert "sequencing_construct" in codes(report)


def test_order_of_entries_carries_no_meaning(business_copy):
    original = load_specification(business_copy(DENTAL, folder="a"))
    swapped = load_specification(business_copy(DENTAL, folder="b", replace=[
        ('obligations = ["patient_name", "contact_email", "visit_type", "preferred_date", "preferred_time"]',
         'obligations = ["preferred_time", "visit_type", "patient_name", "preferred_date", "contact_email"]')]))
    assert original.version == swapped.version


# --- FR21 / FR30: content-addressed versions ------------------------------------------

def test_version_is_the_content_not_the_folder(business_copy):
    a = load_specification(business_copy(DENTAL, folder="first"))
    b = load_specification(business_copy(DENTAL, folder="second/deeper"))
    assert a.version == b.version


def test_editing_the_specification_changes_the_version(business_copy):
    a = load_specification(business_copy(DENTAL, folder="a"))
    b = load_specification(business_copy(DENTAL, folder="b", replace=[("refusal_sample_rate = 0.2", "refusal_sample_rate = 0.3")]))
    assert a.version != b.version


def test_editing_a_source_changes_the_version(business_copy):
    a = load_specification(business_copy(DENTAL, folder="a"))
    path = business_copy(DENTAL, folder="b")
    guide = path.parent / "knowledge" / "practice-guide.md"
    guide.write_text(guide.read_text(encoding="utf-8").replace("95 dollars", "99 dollars"), encoding="utf-8")
    assert load_specification(path).version != a.version


def test_an_unreadable_source_blocks_and_nothing_from_it_is_used(business_copy):
    spec = business_copy(DENTAL, replace=[('path = "knowledge/practice-guide.md"', 'path = "knowledge/missing.md"')])
    loaded = load_specification(spec)
    assert loaded.sources == {}
    report = validate(loaded)
    assert "source_unreadable" in codes(report)


# --- FR51, FR52, FR109, FR16: capability contracts -------------------------------------

def test_effect_without_success_evidence_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[('success_evidence = "read_back"\n', "")])
    assert "no_success_evidence" in codes(validate(load_specification(spec)))


def test_effect_without_consequence_class_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[
        ("consequence = { reversible = true, costs_money = false, reaches_customer = true }\n", "")])
    assert "no_consequence_class" in codes(validate(load_specification(spec)))


def test_consequential_effect_without_authority_basis_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[('authority_basis = "requester_self"\n', "")])
    assert "no_authority_basis" in codes(validate(load_specification(spec)))


def test_liability_capability_must_require_operator_approval(business_copy):
    spec = business_copy(DENTAL, replace=[('authority_class = "state_changing"', 'authority_class = "liability"')])
    assert "liability_without_operator" in codes(validate(load_specification(spec)))


# --- FR23: granted but always denied -----------------------------------------------------

def test_granted_but_always_denied_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[(
        'deny_when = [{ fact = "preferred_date", op = "weekday_in", value = ["sunday"] }]',
        'deny_when = [{ fact = "patient_name", op = "present" }]')])
    report = validate(load_specification(spec))
    assert "granted_but_always_denied" in codes(report)


def test_explicit_always_deny_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[
        ('id = "no_sunday_visits"\n', 'id = "no_sunday_visits"\nalways_deny = true\n')])
    assert "granted_but_always_denied" in codes(validate(load_specification(spec)))


def test_a_narrow_rule_is_not_reported_as_always_denying(business_copy):
    report = validate(load_specification(business_copy(DENTAL)))
    assert "granted_but_always_denied" not in codes(report)


# --- references, uniqueness, guards ---------------------------------------------------------

def test_obligation_naming_an_undeclared_fact_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[('"preferred_date", "preferred_time"]', '"preferred_date", "insurer"]')])
    assert "unresolved_reference" in codes(validate(load_specification(spec)))


def test_a_fact_cannot_be_both_obligation_and_diagnostic(business_copy):
    spec = business_copy(DENTAL, replace=[('diagnostic_inputs = ["symptoms"]\n', 'diagnostic_inputs = ["patient_name"]\n')])
    assert "obligation_and_diagnostic" in codes(validate(load_specification(spec)))


def test_guard_without_detector_blocks(business_copy):
    spec = business_copy(DENTAL, replace=[
        ('detect_keywords = ["severe pain", "unbearable", "swollen", "swelling", "fever"]', "detect_keywords = []")])
    assert "guard_without_detector" in codes(validate(load_specification(spec)))


def test_unknown_field_is_rejected(business_copy):
    spec = business_copy(DENTAL, replace=[('name = "Bright Smile Dental"', 'name = "Bright Smile Dental"\nprompt = "Be nice"')])
    with pytest.raises(SpecificationError) as exc:
        load_specification(spec)
    assert exc.value.findings[0].code == "unknown_field"


def test_not_toml_is_a_stated_outcome(tmp_path):
    bad = tmp_path / "specification.toml"
    bad.write_text("this is = = not toml", encoding="utf-8")
    with pytest.raises(SpecificationError) as exc:
        load_specification(bad)
    assert exc.value.findings[0].code == "not_toml"


# --- AD-4: one artifact, three projections ----------------------------------------------------

def test_compile_refuses_a_specification_that_fails_the_gate(business_copy):
    spec = business_copy(DENTAL, replace=[('success_evidence = "read_back"\n', "")])
    with pytest.raises(SpecificationError) as exc:
        compile_specification(load_specification(spec))
    assert any(f.code == "no_success_evidence" for f in exc.value.findings)


def test_projections_come_from_one_artifact(business_copy):
    loaded = load_specification(business_copy(DENTAL))
    compiled = compile_specification(loaded)
    assert compiled.spec_version == loaded.version
    assert compiled.compiler_version == COMPILER_VERSION
    assert compiled.surface.names() == set(compiled.policy.capabilities)
    assert compiled.context.tenant == compiled.policy.tenant == "bright-smile-dental"
    origins = {i.origin for i in compiled.context.items}
    assert origins == {"specification", "source"}
    source_items = [i for i in compiled.context.items if i.origin == "source"]
    assert all(i.source_version == loaded.sources["practice_guide"].content_hash for i in source_items)
    book = compiled.policy.capabilities["book_visit"]
    assert book.confirmation and book.idempotent and book.authority_basis == "requester_self"
    assert [r.rule_id for r in book.deny_rules] == ["bookable_visit_types", "no_sunday_visits"]
    assert compiled.policy.never_ask_facts == {"medical_history"}
    assert compiled.policy.conclusions == {"describe_procedure_generally": True, "diagnose_condition": False}
