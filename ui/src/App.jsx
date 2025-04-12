import React from "react";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">HomeyMind Dashboard</h1>

        <div className="bg-white rounded-xl p-4 shadow mb-4">
          <p className="mb-2">Status: <span className="text-green-600">Actief</span></p>
          <button
            onClick={() => alert("Testprompt verzonden")}
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            Stuur testprompt
          </button>
        </div>

        <div className="bg-white rounded-xl p-4 shadow">
          <h2 className="text-xl font-semibold mb-2">Laatste acties</h2>
          <ul className="text-sm text-gray-700">
            <li>[08:41] 🧠 Switched naar GPT-4o</li>
            <li>[08:40] 💡 Zet woonkamerlamp aan</li>
            <li>[08:39] 🎤 Wake word gedetecteerd</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
