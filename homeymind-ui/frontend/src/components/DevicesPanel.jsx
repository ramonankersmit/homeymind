import React, { useState } from 'react';
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";

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

export default function DevicesPanel({ devices = [], onRefresh, lastFetched }) {
  const [hoveredDevice, setHoveredDevice] = useState(null);

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
        <Button
          onClick={onRefresh}
          className="text-gray-400 hover:text-white flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-800"
        >
          <span>↻</span>
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {devices.map((device, index) => (
          <Card 
            key={index} 
            className="bg-gray-800/50 border-gray-700/50 hover:bg-gray-700/50 transition-all duration-200"
            onMouseEnter={() => setHoveredDevice(device.id)}
            onMouseLeave={() => setHoveredDevice(null)}
          >
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {DEVICE_ICONS[device.type] || DEVICE_ICONS.default}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-white">{device.name}</p>
                  <p className="text-gray-400 text-sm">{device.id}</p>
                </div>
              </div>
              
              {/* Capability icons */}
              <div className="flex gap-1 mt-2">
                {device.capabilities && Object.entries(device.capabilities).map(([capability, value]) => (
                  <div 
                    key={capability}
                    className="text-sm opacity-75"
                    title={`${capability}: ${value ? 'enabled' : 'disabled'}`}
                  >
                    {CAPABILITY_ICONS[capability] || '🔧'}
                  </div>
                ))}
              </div>
              
              {/* Detailed capabilities on hover */}
              {hoveredDevice === device.id && device.capabilities && (
                <div className="mt-2 pt-2 border-t border-gray-700/50">
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(device.capabilities).map(([capability, value]) => (
                      <div 
                        key={capability}
                        className="flex items-center gap-1 text-sm bg-gray-900/50 px-2 py-1 rounded"
                      >
                        <span>{CAPABILITY_ICONS[capability] || '🔧'}</span>
                        <span className="text-gray-300">{capability}</span>
                        {typeof value === 'boolean' && (
                          <span className={`ml-1 ${value ? 'text-green-400' : 'text-red-400'}`}>
                            {value ? '✓' : '✕'}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 