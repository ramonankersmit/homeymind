import React from 'react';

export function Card({ className, children, ...props }) {
  return (
    <div className={`rounded-lg border bg-card text-card-foreground shadow-sm p-4 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardContent({ className, children, ...props }) {
  return (
    <div className={`p-2 pt-0 ${className}`} {...props}>
      {children}
    </div>
  );
} 