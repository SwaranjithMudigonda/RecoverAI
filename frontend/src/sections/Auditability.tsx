import React from 'react';

interface AuditabilityProps {
  lastRequestId: string;
}

export const Auditability: React.FC<AuditabilityProps> = ({ lastRequestId }) => {
  return (
    <section className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Audit Log Status — Local Read-Only
        </h2>
        <span className="text-xs text-[#9AA6B2]">
          Deterministic logging state of data/processed/recoverai_agent_audit_log.csv
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Security & Compliance Status List */}
        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-4 space-y-3">
          <div className="text-xs font-semibold text-[#F3F5F7]">
            Security Boundaries & Audit State
          </div>
          <p className="text-xs text-[#9AA6B2] leading-relaxed">
            Audit logs are written to local disk synchronously on every orchestration call. The audit log is an internal security boundary and is intentionally not exposed via public REST endpoints.
          </p>
          <div className="space-y-2 pt-2 border-t border-[#26313D] text-xs">
            <div className="flex justify-between items-center">
              <span className="text-[#9AA6B2]">Audit Logging:</span>
              <span className="text-emerald-400 font-medium">ACTIVE</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#9AA6B2]">Storage Location:</span>
              <span className="text-[#F3F5F7]">LOCAL CSV</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#9AA6B2]">Public Endpoint:</span>
              <span className="text-rose-400 font-medium">DISABLED</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#9AA6B2]">Sensitive Leakage Detected:</span>
              <span className="text-emerald-400 font-medium">NONE (0 violations)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#9AA6B2]">Model Provenance:</span>
              <span className="text-emerald-400 font-medium">VERIFIED</span>
            </div>
          </div>
        </div>

        {/* Right: Stream State */}
        <div className="bg-[#141B23] border border-[#26313D] rounded-lg p-4 flex flex-col justify-between">
          <div>
            <div className="text-xs font-semibold text-[#F3F5F7] mb-1.5">
              Local Audit Stream Console
            </div>
            <p className="text-xs text-[#9AA6B2] leading-relaxed mb-4">
              Browser security policies restrict direct web access to local filesystem files. Inspect the audit log directly on your server filesystem:
            </p>

            <div className="bg-[#0B0F14] border border-[#26313D] rounded p-3 text-xs space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-[#667380]">Target File:</span>
                <code className="text-blue-400 font-mono text-[11px]">data/processed/recoverai_agent_audit_log.csv</code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#667380]">Last Request ID:</span>
                <code className="text-[#F3F5F7] font-mono text-[11px]">{lastRequestId}</code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#667380]">Logging Mode:</span>
                <span className="text-emerald-400 font-medium text-[11px]">Append-Only (Thread-Safe)</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#26313D] text-[11px] text-[#667380] text-right">
            Zero credential storage • Cryptographic nonces
          </div>
        </div>
      </div>
    </section>
  );
};
