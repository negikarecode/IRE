# AI Recommendation Standardization

## Overview

All AI recommendations across the platform now follow a standardized, auditable format to ensure explainability and transparency. This eliminates "AI thinks..." responses and provides users with clear, actionable insights.

## Standardized Format

Every AI recommendation includes the following fields:

### 1. Issue
Clear description of the problem detected.

**Example:** "ICD code 'V87.0' has been deleted and is no longer valid."

### 2. Evidence
Specific evidence supporting the finding, extracted from source documents.

**Example:** "Code 'V87.0' found in diagnosis field of discharge summary."

### 3. Relevant Extracted Fields
Key fields from extracted data that led to this conclusion.

**Example:**
```json
{
  "code_type": "ICD",
  "code_value": "V87.0",
  "diagnosis_text": "Patient presented with...",
  "severity": "critical"
}
```

### 4. Supporting Documents
Document IDs or names that contain the evidence.

**Example:** ["Discharge Summary", "Clinical Notes"]

### 5. Reasoning
Step-by-step explanation of how AI reached this conclusion.

**Example:** "1. Validated ICD code format. 2. Checked against deleted code database. 3. Found code 'V87.0' in deleted list. 4. Confirmed code is no longer valid per ICD-10-CM guidelines."

### 6. Recommended Action
Specific action to address the issue.

**Example:** "Use the current valid ICD code for this diagnosis. Refer to ICD-10-CM official coding guidelines."

### 7. Confidence
Confidence score (0.0 to 1.0) indicating certainty of the finding.

**Example:** 0.95

## Implementation

### Base Class
`app/infrastructure/base/ai_recommendation.py` provides:
- `AIRecommendation` data model
- `RecommendationBuilder` helper class
- Conversion methods for different finding types

### Service Integration

All AI services now convert their findings to the standardized format:

1. **Validation Service** (`validation_service.py`)
   - Converts validation findings to standardized format
   - Includes evidence from document review
   - Provides clear reasoning for each validation rule

2. **Coding Review Service** (`coding_review_service.py`)
   - Converts coding review findings to standardized format
   - Includes medical evidence from clinical documentation
   - References official coding guidelines in reasoning

3. **Denial Prediction Service** (`denial_prediction_service.py`)
   - Converts risk factors to standardized format
   - Explains weight and impact of each factor
   - Provides historical pattern context

4. **Revenue Leakage Service** (`revenue_leakage_service.py`)
   - Converts leakage findings to standardized format
   - Includes revenue impact calculations
   - Provides specific correction recommendations

## Auditability Features

### Traceability
- Every finding references source documents
- Evidence snippets preserved from original text
- Page numbers and document IDs tracked

### Explainability
- Step-by-step reasoning for each conclusion
- Reference to rules/guidelines applied
- Clear distinction between detected issue and recommended action

### Transparency
- Confidence scores clearly stated
- Multiple evidence sources when available
- Alternative explanations considered

## Example Output

### Before (Non-Standard)
```json
{
  "detected_issue": "Invalid ICD code",
  "explanation": "Code is invalid",
  "recommended_fix": "Fix the code",
  "confidence": 0.9
}
```

### After (Standardized)
```json
{
  "issue": "ICD code 'V87.0' has been deleted and is no longer valid",
  "evidence": "Code 'V87.0' found in diagnosis field of discharge summary (page 3)",
  "relevant_extracted_fields": {
    "code_type": "ICD",
    "code_value": "V87.0",
    "diagnosis_text": "Patient presented with...",
    "severity": "critical"
  },
  "supporting_documents": ["Discharge Summary"],
  "reasoning": "1. Validated ICD code format against ICD-10 pattern. 2. Checked code against official deleted code database. 3. Found code 'V87.0' in deleted list (deleted in ICD-10). 4. Confirmed code is no longer valid per ICD-10-CM Official Guidelines. 5. This code will result in automatic claim denial.",
  "recommended_action": "Replace ICD code 'V87.0' with current valid code for this diagnosis. Refer to ICD-10-CM Official Guidelines for appropriate code selection.",
  "confidence": 0.95
}
```

## Benefits

1. **No "AI thinks..." responses** - All recommendations are structured and explainable
2. **Full audit trail** - Every decision can be traced back to source documents
3. **User trust** - Clear reasoning builds confidence in AI recommendations
4. **Actionable insights** - Specific recommended actions guide users
5. **Compliance** - Meets regulatory requirements for AI explainability
6. **Debugging** - Easier to identify and fix issues in AI logic

## Usage in API Responses

All API endpoints now return findings in the standardized format:

- `POST /validation/validate` - Validation findings
- `POST /coding-review/review` - Coding review findings
- `POST /denial-prediction/predict` - Denial risk factors
- `POST /revenue-leakage/detect` - Revenue leakage findings

## Future Enhancements

- Add user feedback mechanism to improve reasoning
- Include confidence intervals for probabilistic findings
- Add alternative recommendations with trade-offs
- Implement recommendation versioning for audit trails
