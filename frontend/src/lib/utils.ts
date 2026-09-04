import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useState, useEffect } from 'react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type CurrencyMode = 'INR' | 'BRL';

let currentCurrency: CurrencyMode =
  typeof window !== 'undefined'
    ? ((localStorage.getItem('recoverai_currency') as CurrencyMode) || 'INR')
    : 'INR';

export function getCurrencyMode(): CurrencyMode {
  return currentCurrency;
}

export function setCurrencyMode(mode: CurrencyMode) {
  currentCurrency = mode;
  if (typeof window !== 'undefined') {
    localStorage.setItem('recoverai_currency', mode);
    window.dispatchEvent(new CustomEvent('currency_change', { detail: mode }));
  }
}

export function useCurrency() {
  const [currency, setCurrency] = useState<CurrencyMode>(getCurrencyMode());

  useEffect(() => {
    const handler = (e: any) => {
      setCurrency(e.detail || getCurrencyMode());
    };
    window.addEventListener('currency_change', handler);
    return () => window.removeEventListener('currency_change', handler);
  }, []);

  const toggleCurrency = () => {
    const next = currency === 'INR' ? 'BRL' : 'INR';
    setCurrencyMode(next);
  };

  return { currency, setCurrency: setCurrencyMode, toggleCurrency };
}

// 1 BRL ≈ 15.00 INR (approximate purchasing power parity conversion)
export const BRL_TO_INR_RATE = 15.0;

export function formatBRL(val: number): string {
  if (currentCurrency === 'INR') {
    const inrVal = val * BRL_TO_INR_RATE;
    return `₹ ${inrVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `R$ ${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatPercent(val: number): string {
  return `${(val * 100).toFixed(1)}%`;
}
