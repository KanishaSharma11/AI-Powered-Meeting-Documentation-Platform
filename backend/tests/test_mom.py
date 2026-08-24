from app.schemas.mom import (
    MOMDecision,
    MOMDocument,
    MOMRequirement,
)


def test_mom_requirement():

    requirement = MOMRequirement(
        text=(
            "The application must support OTP-based "
            "login for all external users."
        )
    )

    assert requirement.text == (
        "The application must support OTP-based "
        "login for all external users."
    )


def test_mom_decision():

    decision = MOMDecision(
        text=(
            "OTP authentication will be mandatory."
        )
    )

    assert decision.text == (
        "OTP authentication will be mandatory."
    )


def test_empty_mom():

    mom = MOMDocument()

    assert mom.meeting_title == "Meeting Minutes"
    assert mom.meeting_date is None
    assert mom.participants == []
    assert mom.requirements == []
    assert mom.decisions == []


def test_complete_mom():

    mom = MOMDocument(
        meeting_title="Authentication Meeting",
        meeting_date="2026-08-13",
        participants=[
            "Sarah",
            "John",
        ],
        requirements=[
            MOMRequirement(
                text=(
                    "The application must support "
                    "OTP-based login."
                )
            )
        ],
        decisions=[
            MOMDecision(
                text=(
                    "OTP authentication will be mandatory."
                )
            )
        ],
    )

    assert mom.meeting_title == (
        "Authentication Meeting"
    )

    assert mom.meeting_date == "2026-08-13"

    assert mom.participants == [
        "Sarah",
        "John",
    ]

    assert len(mom.requirements) == 1

    assert len(mom.decisions) == 1

    assert mom.requirements[0].text == (
        "The application must support OTP-based login."
    )

    assert mom.decisions[0].text == (
        "OTP authentication will be mandatory."
    )