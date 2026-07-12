const API_PREFIX = '/api/v1';

export const endpoints = {
  policies: {
    presets: `${API_PREFIX}/policies/presets`,
    select: `${API_PREFIX}/policies/select`,
    upload: `${API_PREFIX}/policies/upload`,
    my: `${API_PREFIX}/policies/my`,
    source: (policyId: string) => `${API_PREFIX}/policies/${policyId}/source`,
    parse: (policyId: string) => `${API_PREFIX}/policies/${policyId}/parse`,
  },
  cases: {
    create: `${API_PREFIX}/cases`,
    payment: (caseId: string) => `${API_PREFIX}/cases/${caseId}/payment`,
    medicalDetailStatement: (caseId: string) =>
      `${API_PREFIX}/cases/${caseId}/medical-detail-statement`,
    answers: (caseId: string) => `${API_PREFIX}/cases/${caseId}/answers`,
    dashboard: (caseId: string) => `${API_PREFIX}/cases/${caseId}/dashboard`,
    extractedInfo: (caseId: string) => `${API_PREFIX}/cases/${caseId}/extracted-info`,
  },
  analysis: {
    search: `${API_PREFIX}/analysis/search`,
    judge: `${API_PREFIX}/analysis/judge`,
    compare: `${API_PREFIX}/analysis/compare`,
  },
  diseases: {
    search: `${API_PREFIX}/diseases/search`,
  },
} as const;
