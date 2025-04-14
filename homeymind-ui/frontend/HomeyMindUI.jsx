import { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function HomeyMindUI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", message: input };
    setMessages((prev) => [...prev, userMessage]);

    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input })
    });

    const data = await response.json();
    setMessages((prev) => [...prev, { sender: "agent", message: data.response }]);
    setInput("");
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl p-6 flex flex-col gap-4">
        <h1 className="text-xl font-bold">🤖 HomeyMind</h1>

        <div className="flex flex-col gap-2 max-h-[400px] overflow-y-auto">
          {messages.map((msg, idx) => (
            <Card key={idx} className={msg.sender === 'user' ? 'self-end bg-blue-100' : 'self-start bg-gray-200'}>
              <CardContent>
                <p><strong>{msg.sender === 'user' ? 'Jij' : 'Agent'}:</strong> {msg.message}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Typ een opdracht..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <Button onClick={sendMessage}>Verzend</Button>
        </div>
      </div>
    </div>
  );
}
