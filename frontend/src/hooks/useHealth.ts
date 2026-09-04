import { useState, useEffect, useCallback } from 'react';
import { fetchHealth } from '../lib/api';
import type { HealthResponse } from '../types/recovery';

export function useHealth() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
      setIsOnline(true);
      setLastChecked(new Date());
    } catch {
      setIsOnline(false);
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const timer = setInterval(checkHealth, 15000);
    return () => clearInterval(timer);
  }, [checkHealth]);

  return { health, isOnline, lastChecked, refetch: checkHealth };
}
