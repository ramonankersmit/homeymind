import React, { useEffect } from 'react';

export default function Notification({ message, onClose, type = 'error' }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'error' ? 'bg-red-600' : 'bg-green-600';

  return (
    <div className={`absolute top-4 left-1/2 transform -translate-x-1/2 ${bgColor} text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 z-50`}>
      <span>{message}</span>
      <button
        onClick={onClose}
        className="hover:bg-white/20 rounded-full p-1"
      >
        ✕
      </button>
    </div>
  );
} 