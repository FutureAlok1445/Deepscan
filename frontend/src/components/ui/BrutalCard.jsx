import React from 'react';

export default function BrutalCard({
  children,
  className = '',
  hover = true,
  glow = false,
  as: Tag = 'div',
  ...props
}) {
  return (
    <Tag
      className={`
        bg-ds-card border-3 border-ds-silver/30 p-6
        brutal-shadow
        ${hover ? 'transition-transform duration-200 hover:-translate-y-1 hover:shadow-brutal-lg' : ''}
        ${glow ? 'shadow-brutal-glow' : ''}
        ${className}
      `}
      {...props}
    >
      {children}
    </Tag>
  );
}
