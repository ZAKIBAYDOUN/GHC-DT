import { useState, useEffect } from 'react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8001';

export default function Home() {
  const [audience, setAudience] = useState('public');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/history`)
      .then((res) => res.json())
      .then((data) => setHistory(data));
  }, []);

  const sendMessage = async () => {
    const response = await fetch(`${BACKEND_URL}/api/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audience, question }),
    });
    const data = await response.json();
    setMessages((prev) => [...prev, { role: 'user', content: question }, { role: 'assistant', content: data }]);
    setQuestion('');
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <header className="text-center mb-6">
        <h1 className="text-2xl font-bold">🌿 Green Hill Canarias — AI Portal</h1>
      </header>

      <main className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <section className="md:col-span-2 bg-white p-4 rounded shadow">
          <div className="mb-4">
            <label htmlFor="audience" className="block text-sm font-medium">Select Audience</label>
            <select
              id="audience"
              value={audience}
              onChange={(e) => setAudience(e.target.value)}
              className="mt-1 block w-full border rounded px-3 py-2"
            >
              <option value="boardroom">Boardroom</option>
              <option value="investor">Investor</option>
              <option value="public">Public</option>
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="question" className="block text-sm font-medium">Your Question</label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="mt-1 block w-full border rounded px-3 py-2"
            ></textarea>
          </div>

          <button
            onClick={sendMessage}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Send
          </button>

          <div className="mt-4">
            <h2 className="text-lg font-medium">Chat</h2>
            <ul className="space-y-2">
              {messages.map((msg, index) => (
                <li key={index} className={msg.role === 'user' ? 'text-right' : 'text-left'}>
                  <span className={`inline-block px-3 py-2 rounded ${msg.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'}`}>{msg.content}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <aside className="bg-white p-4 rounded shadow">
          <h2 className="text-lg font-medium">History</h2>
          <pre className="text-sm overflow-auto max-h-64 bg-gray-50 p-2 rounded">
            {JSON.stringify(history, null, 2)}
          </pre>
        </aside>
      </main>
    </div>
  );
}