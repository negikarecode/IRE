export interface User {
  id: string;
  email: string;
  full_name: string;
  tenant_id: string;
  roles: string[];
}

export interface Hospital {
  id: string;
  tenant_id: string;
  name: string;
  npi_number: string;
  facility_type: string;
  created_at: string;
}

export interface Patient {
  id: string;
  tenant_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  dob: string;
  created_at: string;
}

export interface Claim {
  id: string;
  tenant_id: string;
  patient_id: string;
  external_claim_ref: string;
  status: string;
  amount: number;
  created_at: string;
}

export interface RuleDefinition {
  rule_id: string;
  name: string;
  version: string;
  condition: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  explanation: string;
  suggestion: string;
  priority: number;
}
