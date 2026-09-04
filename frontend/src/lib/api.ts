import type { PaymentContext, RecommendationResponse, HealthResponse } from '../types/recovery';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchRecommendation(context: PaymentContext): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/recommend`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(context),
  });

  if (!res.ok) {
    let errBody: any = null;
    try {
      errBody = await res.json();
    } catch {
      // ignore
    }
    const message = errBody?.message || `API request failed with HTTP ${res.status}`;
    const error = new Error(message) as any;
    error.status = res.status;
    error.responseBody = errBody;
    throw error;
  }

  return res.json();
}
