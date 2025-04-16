import React, { useState } from 'react';
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Loader2 } from "lucide-react";

const DEVICE_ICONS = {
  'light': '💡',
  'switch': '🔌',
  'sensor': '📊',
  'thermostat': '🌡️',
  'default': '📱'
};

const CAPABILITY_ICONS = {
  'onoff': '⚡',
  'dim': '🔆',
  'color': '🎨',
  'temperature': '🌡️',
  'setpoint': '🎯',
  'mode': '⚙️'
};

export default function DevicesPanel({ devices = [], onRefresh, lastFetched, isLoading }) {
  const [hoveredDevice, setHoveredDevice] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      const response = await fetch('http://localhost:8000/devices/refresh', {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to refresh devices');
      }
      
      // Wait a bit to allow MQTT messages to be processed
      await onRefresh();
      
      // Set a timeout to do another refresh to ensure we got the latest data
      setTimeout(async () => {
        await onRefresh();
        setIsRefreshing(false);
      }, 2000);
      
    } catch (error) {
      console.error('Error refreshing devices:', error);
      setIsRefreshing(false);
      if (window.showNotification) {
        window.showNotification({
          type: 'error',
          message: 'Fout bij het verversen van apparaten',
          details: error.message
        });
      }
    }
  };

  return (
    <div className="h-full bg-[#0f1218] flex flex-col">
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Beschikbare Apparaten</h2>
          <div className="text-sm text-gray-400 mt-1">
            <p>{devices.length} apparaten gevonden</p>
            {lastFetched && (
              <p>Laatst bijgewerkt: {lastFetched}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="text-gray-400 hover:text-white hover:bg-gray-800"
          >
            {(isRefreshing || isLoading) ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                {isRefreshing ? 'Verversen...' : 'Laden...'}
              </>
            ) : (
              <>
                <span className="mr-2">🔄</span>
                Ververs
              </>
            )}
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {(isLoading || isRefreshing) ? (
          <div className="flex flex-col items-center justify-center h-full">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <p className="text-gray-400 mt-4">Apparaten ophalen...</p>
          </div>
        ) : devices.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>Geen apparaten gevonden</p>
            <p className="text-sm mt-2">Klik op ververs om opnieuw te proberen</p>
          </div>
        ) : (
          <div className="space-y-4">
            {devices.map((device) => (
              <Card key={device.id} className="bg-gray-800/50 border-gray-700/50 hover:bg-gray-700/50 transition-all duration-200">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-white">{device.name}</h3>
                      <p className="text-sm text-gray-400">{device.type}</p>
                      <div className="mt-2">
                        {device.capabilities && device.capabilities.map((capability) => (
                          <span
                            key={capability}
                            className="inline-block px-2 py-1 mr-2 mb-2 text-xs rounded-full bg-gray-700 text-gray-300"
                          >
                            {capability}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">
                        {device.state && Object.entries(device.state).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            {key}: {typeof value === 'boolean' ? (value ? 'Aan' : 'Uit') : value}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 