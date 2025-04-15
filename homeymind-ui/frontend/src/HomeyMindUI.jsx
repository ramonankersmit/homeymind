import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import DevicesPanel from './components/DevicesPanel';
import Notification from './components/Notification';

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
      <Card className="mb-4 bg-blue-100 text-gray-900">
        <CardContent className="flex flex-col gap-2 p-4">
          <div className="flex items-center gap-2">
            <span role="img" aria-label={mainMessage.role} className="text-xl">
              {AGENT_ICONS[mainMessage.role] || AGENT_ICONS.default}
            </span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                {mainMessage.timestamp && (
                  <span className="text-xs text-gray-600">
                    {mainMessage.timestamp}
                  </span>
                )}
                <p className="font-semibold text-sm text-gray-900">Jij</p>
              </div>
              <p className="whitespace-pre-wrap text-gray-900">{mainMessage.message}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Agent response with thinking process
  return (
    <div className="mb-4">
      <Card className={isLoading ? "bg-gray-100 border border-gray-300 text-gray-900" : "bg-white text-gray-900"}>
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
                  <p className="font-semibold text-sm text-gray-600">
                    {isLoading ? "Denkproces" : "Antwoord"}
                  </p>
                </div>
                {agentMessages.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-gray-500 flex items-center gap-2 hover:bg-gray-100"
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
            <div className="flex items-center gap-2 text-gray-500 ml-8">
              <div className="animate-spin h-4 w-4 border-2 border-gray-500 rounded-full border-t-transparent"></div>
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
                        <p className="text-xs text-gray-600">
                          {msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}
                        </p>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Divider line */}
          {isExpanded && agentMessages.length > 0 && finalResponse && (
            <div className="my-4 border-t border-gray-200"></div>
          )}

          {/* Final response */}
          {finalResponse && !isLoading && (
            <div className="ml-8">
              <p className="whitespace-pre-wrap">{finalResponse.message}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default function HomeyMindUI() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [devices, setDevices] = useState([]);
  const [isRefreshingDevices, setIsRefreshingDevices] = useState(false);
  const [lastFetched, setLastFetched] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  const fetchDevices = useCallback(async () => {
    try {
      setIsRefreshingDevices(true);
      const response = await fetch('http://localhost:8000/devices');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Fetched devices data:', data); // Debug log for entire response
      if (Array.isArray(data.devices)) {
        setDevices(data.devices);
        // Set the current time as the last fetched time
        const now = new Date();
        setLastFetched(now.toLocaleTimeString('nl-NL', { 
          hour: '2-digit', 
          minute: '2-digit',
          second: '2-digit'
        }));
      } else {
        console.error('Devices data is not an array:', data);
        setDevices([]);
      }
      // Handle error or warning from backend
      if (data.error) {
        console.log('Error data received:', data.error); // Debug log for error
        if (typeof data.error === 'object' && data.error.message) {
          console.log('Setting error message:', data.error.message); // Debug log for message
          setError(data.error.message);
        } else {
          console.log('Setting error string:', data.error); // Debug log for string error
          setError(data.error);
        }
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
      setDevices([]);
      setError('Kon geen verbinding maken met de server');
    } finally {
      setIsRefreshingDevices(false);
    }
  }, []);

  // Fetch devices on component mount
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

  return (
    <div className="flex h-screen bg-gray-900 text-white p-4 gap-4">
      {/* Watermark Logo */}
      <div className="absolute inset-0 flex items-center justify-center opacity-5 pointer-events-none">
        <div className="flex items-center gap-4 transform scale-150">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 transform translate-x-2"></div>
          </div>
          <div className="text-6xl font-bold tracking-wider text-white">HomeyMind</div>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col relative">
        {/* Error Notification */}
        {error && (
          <Notification
            message={error}
            onClose={() => setError(null)}
            type="error"
          />
        )}

        {/* Clear Session Button */}
        <div className="flex justify-end mb-4">
          <Button
            variant="outline"
            onClick={clearSession}
            className="text-white border-gray-700 hover:bg-gray-800"
            disabled={isLoading || messages.length === 0}
          >
            🗑️ Wis Sessie
          </Button>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto mb-4">
          {groupedMessages.map((group, index) => (
            <MessageGroup
              key={index}
              messages={group}
              isLoading={isLoading && index === groupedMessages.length - 1}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type een bericht..."
            className="flex-1 bg-gray-800 text-white border-gray-700"
            disabled={isLoading}
          />
          <Button
            onClick={sendMessage}
            className="bg-blue-600 text-white hover:bg-blue-700"
            disabled={isLoading || !input.trim()}
          >
            Verstuur
          </Button>
        </div>
      </div>

      {/* Devices Panel */}
      <DevicesPanel 
        devices={devices} 
        onRefresh={fetchDevices}
        lastFetched={lastFetched}
      />
    </div>
  );
} 