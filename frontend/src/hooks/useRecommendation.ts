import { useState, useCallback, useEffect } from 'react';
import { fetchRecommendation } from '../lib/api';
import { PRESETS } from '../data/presets';
import type { PaymentContext, RecommendationResponse, RequestStatus } from '../types/recovery';

export function useRecommendation() {
  const [context, setContext] = useState<PaymentContext>(PRESETS.soft);
  const [activePreset, setActivePreset] = useState<string>('soft');
  const [status, setStatus] = useState<RequestStatus>('IDLE');
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRequestId, setLastRequestId] = useState<string>('NONE');

  const executeRecommendation = useCallback(async (ctxToUse?: PaymentContext) => {
    const targetCtx = ctxToUse || context;
    setStatus('REQUESTING');
    setError(null);

    try {
      const data = await fetchRecommendation(targetCtx);
      setRecommendation(data);
      setStatus('SUCCESS');
      if (data.request_id) {
        setLastRequestId(data.request_id);
      }
    } catch (err: any) {
      setStatus('ERROR');
      setError(err?.message || 'RecoverAI API is offline or unreachable. Please start the local uvicorn server.');
    }
  }, [context]);

  const applyPreset = useCallback((presetKey: string) => {
    const presetData = PRESETS[presetKey];
    if (!presetData) return;
    setActivePreset(presetKey);
    setContext(presetData);
    executeRecommendation(presetData);
  }, [executeRecommendation]);

  const updateContextField = useCallback(<K extends keyof PaymentContext>(field: K, value: PaymentContext[K]) => {
    setActivePreset('');
    setContext(prev => ({ ...prev, [field]: value }));
  }, []);

  // Initial load recommendation
  useEffect(() => {
    executeRecommendation();
  }, [executeRecommendation]);

  return {
    context,
    setContext,
    activePreset,
    status,
    recommendation,
    error,
    lastRequestId,
    applyPreset,
    updateContextField,
    executeRecommendation
  };
}
