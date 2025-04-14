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
    <div className="w-64 bg-gray-800 p-4 rounded-lg h-full overflow-y-auto relative">
      <h2 className="text-lg font-semibold text-white mb-4">Beschikbare Apparaten</h2>
      
      {/* Device count and last fetched time */}
      <div className="mb-4 text-sm text-gray-400">
        <p>{devices.length} apparaten gevonden</p>
        {lastFetched && (
          <p>Laatst bijgewerkt: {lastFetched}</p>
        )}
      </div>
      
      <div className="space-y-2 mb-12">
        {devices.map((device, index) => (
          <Card 
            key={index} 
            className="bg-gray-700 border-gray-600 transition-all duration-200 hover:bg-gray-600 relative"
            onMouseEnter={() => setHoveredDevice(device.id)}
            onMouseLeave={() => setHoveredDevice(null)}
          >
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <span className="text-xl">
                  {DEVICE_ICONS[device.type] || DEVICE_ICONS.default}
                </span>
                <div className="flex-1">
                  <p className="text-white font-medium">{device.name}</p>
                  <p className="text-gray-400 text-sm">{device.id}</p>
                </div>
              </div>
              
              {/* Capability icons at bottom right of each card */}
              {device.capabilities && hoveredDevice !== device.id && (
                <div className="absolute bottom-2 right-2 flex flex-row-reverse gap-1">
                  {Object.entries(device.capabilities).map(([capability, value]) => (
                    <div 
                      key={capability}
                      className="text-sm"
                      title={`${capability}: ${value ? 'enabled' : 'disabled'}`}
                    >
                      {CAPABILITY_ICONS[capability] || '🔧'}
                    </div>
                  ))}
                </div>
              )}
              
              {/* Detailed capabilities on hover */}
              {hoveredDevice === device.id && device.capabilities && (
                <div className="mt-2 pt-2 border-t border-gray-600">
                  <p className="text-sm text-gray-300 mb-1">Capabilities:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(device.capabilities).map(([capability, value]) => (
                      <div 
                        key={capability}
                        className="flex items-center gap-1 text-sm bg-gray-800 px-2 py-1 rounded"
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
      <div className="absolute bottom-4 right-4">
        <Button
          onClick={onRefresh}
          className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg"
          title="Ververs apparaten"
        >
          🔄
        </Button>
      </div>
    </div>
  );
} 