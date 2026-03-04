import React from 'react';

const VARIANTS = {
  primary: 'bg-ds-red text-white border-ds-silver hover:bg-red-700',
  secondary: 'bg-ds-card text-white border-ds-silver hover:bg-ds-silver hover:text-ds-bg',
  ghost: 'bg-transparent text-white border-transparent hover:border-ds-silver',
  danger: 'bg-red-900 text-ds-red border-ds-red hover:bg-ds-red hover:text-white',
  success: 'bg-ds-card text-ds-green border-ds-green hover:bg-ds-green hover:text-ds-bg',
};

const SIZES = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-8 py-3.5 text-base',
};

export default function BrutalButton({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  loading = false,
  as: Tag = 'button',
  ...props
}) {
  return (
    <Tag
      className={`
        inline-flex items-center justify-center gap-2
        font-grotesk font-bold uppercase tracking-wider
        border-3 brutal-shadow
        transition-all duration-200
        ${disabled || loading ? 'opacity-50 cursor-not-allowed' : 'hover:-translate-y-0.5 hover:shadow-brutal-lg active:translate-y-0 active:shadow-none cursor-pointer'}
        ${VARIANTS[variant] || VARIANTS.primary}
        ${SIZES[size] || SIZES.md}
        ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </Tag>
  );
}
