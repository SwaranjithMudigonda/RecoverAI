import React from 'react';

export const SecurityStatus: React.FC = () => {
  const controls = [
    {
      title: 'Sensitive Credential Rejection',
      code: 'HTTP 400',
      desc: 'Rejects card numbers, CVVs, OTPs, PINs, and passwords at boundary middleware.',
    },
    {
      title: 'Leakage Field Defense',
      code: 'HTTP 400',
      desc: 'Rejects post-decision target fields in prediction context to prevent data poisoning.',
    },
    {
      title: 'Bounded Payload Cap',
      code: 'HTTP 413',
      desc: 'Strict 2 MB streaming body threshold prevents memory allocation denial-of-service.',
    },
    {
      title: 'Sliding Rate Limiter',
      code: 'HTTP 429',
      desc: 'Enforces 100 requests / minute per client IP using asyncio sliding window tracking.',
    },
    {
      title: 'Exception Sanitization',
      code: 'HTTP 500',
      desc: 'Zero internal Python stack traces, filesystem paths, or system internals returned to client.',
    },
    {
      title: 'Thread-Safe Local Audit',
      code: 'CSV Stream',
      desc: 'Appends orchestration entries to disk with sensitive fields purged at ingestion.',
    },
  ];

  return (
    <section id="security-audit" className="bg-[#111820] border border-[#26313D] rounded-xl p-5 sm:p-6">
      <div className="pb-4 mb-4 border-b border-[#26313D]">
        <h2 className="text-base font-semibold text-[#F3F5F7]">
          Defensive API Security Controls
        </h2>
        <span className="text-xs text-[#9AA6B2]">
          Enterprise security policies enforced before recommendation processing
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
        {controls.map(c => (
          <div key={c.title} className="bg-[#141B23] border border-[#26313D] rounded-lg p-3.5">
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-xs font-semibold text-[#F3F5F7]">
                {c.title}
              </span>
              <span className="text-[10px] font-mono font-medium text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
                {c.code}
              </span>
            </div>
            <p className="text-xs text-[#9AA6B2] leading-relaxed">
              {c.desc}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};
