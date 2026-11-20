"use client";

import { useId } from "react";

type Props = {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  multiline?: boolean;
  placeholder?: string;
  maxLength?: number;
  type?: string;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
};

export function Field({ label, hint, value, onChange, multiline, placeholder, maxLength = 1200, type = "text", inputMode }: Props) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const near = value.length > maxLength * 0.9;
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-[0.9375rem] font-medium">
        {label}
      </label>
      {hint && (
        <p id={hintId} className="text-[0.8125rem] leading-relaxed text-muted">
          {hint}
        </p>
      )}
      {multiline ? (
        <textarea
          id={id}
          aria-describedby={hintId}
          className="field min-h-[5.5rem] resize-y leading-relaxed"
          value={value}
          placeholder={placeholder}
          maxLength={maxLength}
          rows={3}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          aria-describedby={hintId}
          className="field"
          type={type}
          inputMode={inputMode}
          value={value}
          placeholder={placeholder}
          maxLength={maxLength}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
      {near && (
        <p className="text-xs text-muted" aria-live="polite">
          {value.length}/{maxLength} characters
        </p>
      )}
    </div>
  );
}
