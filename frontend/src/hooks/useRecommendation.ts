import { useState, useCallback, useEffect } from 'react';
import { fetchRecommendation } from '../lib/api';
import { PRESETS } from '../data/presets';
import type { PaymentContext, RecommendationResponse, RequestStatus } from '../types/recovery';

const STORAGE_KEY = 'recoverai_recommendation_state_v1';

function getStoredState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (err) {
    console.warn('Unable to retrieve RecoverAI state from storage:', err);
  }
  return null;
}

export function useRecommendation() {
  const initial = getStoredState();

  const [context, setContext] = useState<PaymentContext>(initial?.context || PRESETS.soft);
  const [activePreset, setActivePreset] = useState<string>(initial?.activePreset ?? '');
  const [status, setStatus] = useState<RequestStatus>(
    initial?.recommendation ? 'SUCCESS' : (initial?.status === 'REQUESTING' ? 'IDLE' : (initial?.status || 'IDLE'))
  );
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(initial?.recommendation ?? null);
  const [error, setError] = useState<string | null>(null);
  const [lastRequestId, setLastRequestId] = useState<string>(initial?.lastRequestId ?? 'NONE');

  // Sync changes to localStorage so refreshing the page preserves all results and inputs
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          context,
          activePreset,
          status,
          recommendation,
          lastRequestId,
        })
      );
    } catch (err) {
      console.warn('Unable to persist RecoverAI state to storage:', err);
    }
  }, [context, activePreset, status, recommendation, lastRequestId]);

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

