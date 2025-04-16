import React, { useEffect } from 'react';
import { X } from 'lucide-react';

const NOTIFICATION_TYPES = {
  error: {
    bgColor: 'bg-red-500',
    icon: '⚠️'
  },
  warning: {
    bgColor: 'bg-yellow-500',
    icon: '⚠️'
  },
  success: {
    bgColor: 'bg-green-500',
    icon: '✅'
  },
  info: {
    bgColor: 'bg-blue-500',
    icon: 'ℹ️'
  }
};

const Notification = ({ type = 'info', message, details, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const notificationStyle = NOTIFICATION_TYPES[type] || NOTIFICATION_TYPES.info;

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-md animate-in slide-in-from-top-2`}>
      <div className={`${notificationStyle.bgColor} text-white p-4 rounded-lg shadow-lg`}>
        <div className="flex items-start gap-3">
          <span className="text-xl">{notificationStyle.icon}</span>
          <div className="flex-1">
            <p className="font-medium">{message}</p>
            {details && (
              <p className="text-sm mt-1 text-white/80">{details}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white focus:outline-none"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Notification; 