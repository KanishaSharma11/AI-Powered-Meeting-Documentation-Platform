from app.ai.agents.requirements_decisions_agent import (
    RequirementsDecisionsAgent,
)


def test_requirements_decisions_agent():

    transcript = """
SEG-0001
Speaker: Sarah
Timestamp: 00:10:15
Text: The application must support OTP-based login
for all external users.

SEG-0002
Speaker: John
Timestamp: 00:10:42
Text: Agreed. OTP authentication will be mandatory.

SEG-0003
Speaker: Sarah
Timestamp: 00:11:10
Text: We are still discussing whether SMS or email
should be used for the OTP.

SEG-0004
Speaker: John
Timestamp: 00:12:00
Text: Let's proceed with SMS for the initial release.
"""

    # ==========================================================
    # Initialize the Requirements + Decisions agent
    # ==========================================================

    agent = RequirementsDecisionsAgent()

    # ==========================================================
    # Run extraction
    # ==========================================================

    result = agent.extract(transcript)

    # ==========================================================
    # Basic result validation
    # ==========================================================

    assert result is not None

    assert len(result.requirements) >= 1

    assert len(result.decisions) >= 1

    # ==========================================================
    # Display extracted requirements
    # ==========================================================

    print(
        "\n========== REQUIREMENTS =========="
    )

    for item in result.requirements:

        print("\nRequirement:")
        print(item.text)

        print("Evidence Segment ID:")
        print(item.evidence.segment_id)

        print("Confidence:")
        print(item.confidence)

    # ==========================================================
    # Display extracted decisions
    # ==========================================================

    print(
        "\n========== DECISIONS =========="
    )

    for item in result.decisions:

        print("\nDecision:")
        print(item.text)

        print("Evidence Segment ID:")
        print(item.evidence.segment_id)

        print("Confidence:")
        print(item.confidence)

    # ==========================================================
    # Validate requirement evidence references
    # ==========================================================

    valid_segment_ids = {
        "SEG-0001",
        "SEG-0002",
        "SEG-0003",
        "SEG-0004",
    }

    for item in result.requirements:

        assert (
            item.evidence.segment_id
            in valid_segment_ids
        )

    # ==========================================================
    # Validate decision evidence references
    # ==========================================================

    for item in result.decisions:

        assert (
            item.evidence.segment_id
            in valid_segment_ids
        )

    # ==========================================================
    # Validate extracted text
    # ==========================================================

    requirement_texts = [
        item.text.lower()
        for item in result.requirements
    ]

    decision_texts = [
        item.text.lower()
        for item in result.decisions
    ]

    # The requirement should relate to OTP login.

    assert any(
        "otp" in text
        for text in requirement_texts
    )

    # At least one decision should relate to OTP
    # authentication or the SMS choice.

    assert any(
        "otp" in text or "sms" in text
        for text in decision_texts
    )

    # ==========================================================
    # Validate confidence
    # ==========================================================

    for item in result.requirements:

        assert 0.0 <= item.confidence <= 1.0

    for item in result.decisions:

        assert 0.0 <= item.confidence <= 1.0