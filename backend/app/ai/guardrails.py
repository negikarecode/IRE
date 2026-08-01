import re
from typing import List, Tuple, Optional

class DomainPolicyViolationException(ValueError):
    """Exception raised when a prompt violates domain restrictions (e.g. medical or insurance content)."""
    pass

class DomainGuardrail:
    """
    Enforces domain policy guardrails for AI Infrastructure:
    - Zero medical prompts / queries / instructions allowed.
    - Zero insurance prompts / queries / instructions allowed.
    - Provider-independent policy enforcement.
    """

    # Comprehensive list of medical domain patterns & keywords
    MEDICAL_PATTERNS: List[re.Pattern] = [
        re.compile(r"\bmedical\b", re.IGNORECASE),
        re.compile(r"\bdiagnosis\b|\bdiagnose\b", re.IGNORECASE),
        re.compile(r"\bclinical\b|\bclinician\b", re.IGNORECASE),
        re.compile(r"\bprescription\b|\bmedication\b|\bpharmacy\b", re.IGNORECASE),
        re.compile(r"\bdoctor\b|\bphysician\b|\bnurse\b|\bhospital\b|\bpatient\b", re.IGNORECASE),
        re.compile(r"\bicd-10\b|\bicd-11\b|\bcpt code\b|\bsnomed\b", re.IGNORECASE),
        re.compile(r"\bhipaa\b|\bhealth record\b|\behr\b|\bemr\b", re.IGNORECASE),
        re.compile(r"\btreatment plan\b|\bsymptoms?\b|\bsurgery\b|\boncology\b|\bcardiology\b", re.IGNORECASE),
    ]

    # Comprehensive list of insurance domain patterns & keywords
    INSURANCE_PATTERNS: List[re.Pattern] = [
        re.compile(r"\binsurance\b|\binsurer\b", re.IGNORECASE),
        re.compile(r"\bunderwriting\b|\bunderwriter\b", re.IGNORECASE),
        re.compile(r"\bclaim\b|\bclaims\b|\bclaimant\b", re.IGNORECASE),
        re.compile(r"\bpolicyholder\b|\bpremium\b|\bdeductible\b|\bcopay\b|\bcoinsurance\b", re.IGNORECASE),
        re.compile(r"\bexplanation of benefits\b|\beob\b", re.IGNORECASE),
        re.compile(r"\bpayer\b|\badjudication\b|\bprior authorization\b", re.IGNORECASE),
        re.compile(r"\bactuary\b|\bactuarial\b|\breinsurance\b", re.IGNORECASE),
    ]

    @classmethod
    def validate_text(cls, text: str, context_name: str = "Input Prompt") -> Tuple[bool, Optional[str]]:
        """
        Validates text against domain guardrails.
        Returns (is_valid, violation_reason).
        """
        if not text:
            return True, None

        # Check medical patterns
        for pattern in cls.MEDICAL_PATTERNS:
            if pattern.search(text):
                match = pattern.search(text).group(0)
                reason = f"{context_name} violates Domain Policy: Medical domain content detected ('{match}'). Medical prompts are prohibited."
                return False, reason

        # Check insurance patterns
        for pattern in cls.INSURANCE_PATTERNS:
            if pattern.search(text):
                match = pattern.search(text).group(0)
                reason = f"{context_name} violates Domain Policy: Insurance domain content detected ('{match}'). Insurance prompts are prohibited."
                return False, reason

        return True, None

    @classmethod
    def enforce_policy(cls, text: str, context_name: str = "Input Prompt") -> None:
        """
        Validates text and raises DomainPolicyViolationException if a forbidden domain keyword is found.
        """
        is_valid, reason = cls.validate_text(text, context_name)
        if not is_valid:
            raise DomainPolicyViolationException(reason)

domain_guardrail = DomainGuardrail()
