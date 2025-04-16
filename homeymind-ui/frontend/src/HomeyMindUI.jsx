import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import DevicesPanel from './components/DevicesPanel';
import Notification from './components/Notification';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

// Agent icons mapping
const AGENT_ICONS = {
  'user': '👤',
  'agent': '🤖',
  'intent_parser': '🔹',
  'planner': '🎯',
  'assistant': '💡',
  'device_controller': '🔌',
  'homey_assistant': '🏠',
  'default': '🤖'
};

const MessageGroup = ({ messages, isLoading }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const mainMessage = messages[messages.length - 1];
  const isAgentResponse = mainMessage.sender === 'agent';
  const agentMessages = messages.filter(m => m.is_subagent || (m.role !== 'agent' && m.role !== 'assistant' && m.role !== 'user'));
  const finalResponse = messages.find(m => (m.role === 'agent' || m.role === 'assistant') && !m.is_subagent);
  
  if (!mainMessage) return null;

  // User message
  if (mainMessage.sender === 'user') {
    return (
      <Card className="mb-4 bg-blue-900/30 text-white">
        <CardContent className="flex flex-col gap-2 p-4">
          <div className="flex items-center gap-2">
            <span role="img" aria-label={mainMessage.role} className="text-xl">
              {AGENT_ICONS[mainMessage.role] || AGENT_ICONS.default}
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                {mainMessage.timestamp && (
                  <span className="text-xs text-gray-400">
                    {mainMessage.timestamp}
                  </span>
                )}
                <p className="font-semibold text-sm text-gray-300">Jij</p>
              </div>
              <p className="whitespace-pre-wrap text-white">{mainMessage.message}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Agent response with thinking process
  return (
    <div className="mb-4">
      <Card className={isLoading ? "bg-gray-800/50 border-gray-700 text-white" : "bg-gray-800 text-white"}>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <span role="img" aria-label={isLoading ? "thinking" : "agent"} className="text-xl">
              {isLoading ? "💭" : AGENT_ICONS.agent}
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2">
                  {finalResponse?.timestamp && !isLoading && (
                    <span className="text-xs text-gray-400">
                      {finalResponse.timestamp}
                    </span>
                  )}
                  <p className="font-semibold text-sm text-gray-300">
                    {isLoading ? "Denkproces" : "Antwoord"}
                  </p>
                </div>
                {agentMessages.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-gray-400 flex items-center gap-2 hover:bg-gray-700"
                  >
                    <span className="text-lg">{isExpanded ? '▼' : '▶'}</span>
                    {isExpanded ? "Verberg denkproces" : "Toon denkproces"}
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 text-gray-400 ml-8">
              <div className="animate-spin h-4 w-4 border-2 border-gray-400 rounded-full border-t-transparent"></div>
              <span className="text-sm">Verwerken...</span>
            </div>
          )}

          {/* Agent messages (denkproces) */}
          {isExpanded && agentMessages.length > 0 && (
            <div className="ml-8">
              {agentMessages.map((msg, idx) => (
                <div key={idx} className="mb-2">
                  <div className="flex items-center gap-2">
                    <span role="img" aria-label={msg.role} className="text-sm">
                      {AGENT_ICONS[msg.role] || AGENT_ICONS.default}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        {msg.timestamp && (
                          <span className="text-xs text-gray-400">
                            {msg.timestamp}
                          </span>
                        )}
                        <p className="text-xs text-gray-400">
                          {msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}
                        </p>
                      </div>
                      <p className="text-sm whitespace-pre-wrap text-gray-300">{msg.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Divider line */}
          {isExpanded && agentMessages.length > 0 && finalResponse && (
            <div className="my-4 border-t border-gray-700"></div>
          )}

          {/* Final response */}
          {finalResponse && !isLoading && (
            <div className="ml-8">
              <p className="whitespace-pre-wrap text-white">{finalResponse.message}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default function HomeyMindUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [zones, setZones] = useState([]);
  const [lastFetched, setLastFetched] = useState(null);
  const [showDevices, setShowDevices] = useState(true);
  const [devicesPanelWidth, setDevicesPanelWidth] = useState(320);
  const [isResizing, setIsResizing] = useState(false);
  const [notification, setNotification] = useState(null);
  const [isLoadingDevices, setIsLoadingDevices] = useState(true);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);
  const lastPanelWidth = useRef(devicesPanelWidth);

  // Add global notification handler
  useEffect(() => {
    window.showNotification = ({ type, message, details }) => {
      setNotification({ type, message, details });
    };
    return () => {
      window.showNotification = undefined;
    };
  }, []);

  // Fetch devices
  const fetchDevices = useCallback(async () => {
    try {
      setIsLoadingDevices(true);
      const response = await fetch('http://localhost:8000/devices');
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch devices');
      }

      setZones(data.zones || []);
      setLastFetched(format(new Date(), 'HH:mm:ss', { locale: nl }));

      // Show warning or success message if present
      if (data.warnings && data.warnings.length > 0) {
        setNotification({
          type: 'warning',
          message: data.warnings[0]
        });
      } else if (data.success) {
        window.showNotification({
          type: 'success',
          message: data.success.message,
          details: data.success.details
        });
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
      window.showNotification({
        type: 'error',
        message: 'Fout bij het ophalen van apparaten',
        details: error.message
      });
    } finally {
      setIsLoadingDevices(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  // Group messages by conversation
  const groupedMessages = messages.reduce((groups, message) => {
    const lastGroup = groups[groups.length - 1];
    
    // Start a new group if:
    // 1. This is the first message
    // 2. Current message is from user
    // 3. Previous group's last message was from user
    if (
      !lastGroup || 
      message.sender === 'user' || 
      lastGroup[lastGroup.length - 1].sender === 'user'
    ) {
      groups.push([message]);
    } else {
      lastGroup.push(message);
    }
    
    return groups;
  }, []);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const addMessage = useCallback((newMessage) => {
    console.log('Adding new message:', newMessage);
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const setupEventSource = useCallback((input) => {
    if (eventSourceRef.current) {
      console.log('Closing existing EventSource connection');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    const encodedMessage = encodeURIComponent(input);
    console.log('Setting up new EventSource connection...');
    const eventSource = new EventSource(`http://localhost:8000/chat?message=${encodedMessage}`);

    eventSource.onopen = () => {
      console.log('EventSource connection opened successfully');
      setIsLoading(true);
    };

    // Handle agent messages
    eventSource.addEventListener('agent_message', (event) => {
      console.log('Agent message event received:', event);
      try {
        const data = JSON.parse(event.data);
        console.log('Processing agent message:', data);
        
        addMessage({
          sender: "agent",
          message: data.message,
          role: data.role || "agent",
          isSubMessage: true,
          timestamp: data.timestamp || new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        });
      } catch (error) {
        console.error('Error parsing agent message:', error);
      }
    }, false);

    eventSource.addEventListener('complete', (event) => {
      console.log('Complete event received:', event);
      try {
        const data = JSON.parse(event.data);
        console.log('Processing completion:', data);

        setIsLoading(false);
        eventSource.close();
      } catch (error) {
        console.error('Error parsing completion:', error);
        setIsLoading(false);
        eventSource.close();
      }
    }, false);

    eventSource.addEventListener('error', (error) => {
      console.error('SSE Error:', error);
      addMessage({
        sender: "agent",
        message: "Er is een fout opgetreden bij het verwerken van je verzoek.",
        role: "agent",
        isError: true,
        timestamp: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      });
      setIsLoading(false);
      eventSource.close();
    }, false);

    eventSourceRef.current = eventSource;
  }, [addMessage]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { 
      sender: "user", 
      message: input, 
      role: "user",
      timestamp: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
    addMessage(userMessage);
    setInput("");
    setIsLoading(true);

    try {
      setupEventSource(input);
    } catch (error) {
      console.error('Error setting up EventSource:', error);
      addMessage({
        sender: "agent",
        message: "Er is een fout opgetreden bij het opzetten van de verbinding.",
        role: "agent",
        timestamp: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      });
      setIsLoading(false);
    }
  }, [input, isLoading, addMessage, setupEventSource]);

  // Clear session function
  const clearSession = useCallback(() => {
    setMessages([]);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Handle resize functionality
  const handleResizeMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
    
    // Store initial mouse position and panel width
    const startX = e.clientX;
    const startWidth = devicesPanelWidth;
    
    const handleMouseMove = (moveEvent) => {
      // Calculate delta and apply it to the starting width
      const delta = startX - moveEvent.clientX;
      const newWidth = Math.min(Math.max(250, startWidth + delta), 600);
      setDevicesPanelWidth(newWidth);
      lastPanelWidth.current = newWidth;
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    // Add listeners immediately on mouse down
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [devicesPanelWidth]);

  // Toggle devices panel with width memory
  const toggleDevicesPanel = useCallback(() => {
    if (!showDevices) {
      const savedWidth = lastPanelWidth.current;
      const validWidth = Math.min(Math.max(250, savedWidth), 600);
      setDevicesPanelWidth(validWidth);
      lastPanelWidth.current = validWidth;
    }
    setShowDevices(!showDevices);
  }, [showDevices]);

  // Initialize lastPanelWidth on mount
  useEffect(() => {
    lastPanelWidth.current = devicesPanelWidth;
  }, []);

  return (
    <div className="flex h-screen bg-[#0f1218]">
      {notification && (
        <Notification
          type={notification.type}
          message={notification.message}
          details={notification.details}
          onClose={() => setNotification(null)}
        />
      )}
      
      {/* Main chat area */}
      <div className="flex-1 flex flex-col relative">
        {/* Watermark Logo */}
        <div className="absolute inset-0 flex items-center justify-center opacity-[0.02] pointer-events-none overflow-hidden">
          <div className="flex items-center gap-4 transform scale-150">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 transform translate-x-2"></div>
            </div>
            <div className="text-6xl font-bold tracking-wider text-white">HomeyMind</div>
          </div>
        </div>

        {/* Chat header */}
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setMessages([])} 
              className="text-gray-400 hover:text-white flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-800"
            >
              <span className="text-lg">🗑</span> Wis Sessie
            </button>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={toggleDevicesPanel}
              className="text-gray-400 hover:text-white flex items-center gap-2 px-3 py-1.5 rounded hover:bg-gray-800"
            >
              <span>🔌</span> {showDevices ? 'Verberg' : 'Toon'} Apparaten
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto p-4" ref={messagesEndRef}>
          {groupedMessages.map((group, index) => (
            <MessageGroup
              key={index}
              messages={group}
              isLoading={isLoading && index === groupedMessages.length - 1}
            />
          ))}
        </div>
        
        {/* Input area */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Type je bericht..."
              className="flex-1 bg-gray-800/50 text-white border-gray-700 focus:border-blue-500"
            />
            <Button 
              onClick={sendMessage} 
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6"
            >
              Verstuur
            </Button>
          </div>
        </div>
      </div>

      {/* Resize handle */}
      {showDevices && (
        <div
          className={`w-1 hover:bg-blue-500 cursor-col-resize transition-colors ${
            isResizing ? 'bg-blue-500' : 'bg-gray-700'
          }`}
          onMouseDown={handleResizeMouseDown}
        />
      )}

      {/* Devices panel */}
      {showDevices && (
        <div 
          style={{ width: `${devicesPanelWidth}px` }} 
          className="border-l border-gray-800 transition-all duration-75 ease-in-out"
        >
          <DevicesPanel
            zones={zones}
            onRefresh={fetchDevices}
            lastFetched={lastFetched}
            isLoading={isLoadingDevices}
          />
        </div>
      )}
    </div>
  );
} 