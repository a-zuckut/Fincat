import React, { useEffect, useState } from 'react';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  notes?: string | null;
}

interface ChatResponse {
  reply: string;
  stocks: Stock[];
}

export const App: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loadingStocks, setLoadingStocks] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<string[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = async () => {
    setLoadingStocks(true);
    setError(null);
    try {
      const res = await fetch('/stocks');
      if (!res.ok) throw new Error('Failed to fetch stocks');
      const data: Stock[] = await res.json();
      setStocks(data);
    } catch (err: any) {
      setError(err.message ?? 'Unknown error fetching stocks');
    } finally {
      setLoadingStocks(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const handleSendChat = async () => {
    const message = chatInput.trim();
    if (!message) return;

    setChatLoading(true);
    setError(null);
    setChatHistory((prev) => [...prev, `You: ${message}`]);
    setChatInput('');

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      if (!res.ok) throw new Error('Chat request failed');
      const data: ChatResponse = await res.json();
      setChatHistory((prev) => [...prev, `Bot: ${data.reply}`]);
      setStocks(data.stocks);
    } catch (err: any) {
      setError(err.message ?? 'Unknown error talking to chatbot');
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChat();
    }
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Fincat Stocks + Chatbot</h1>
      </header>
      <div className="app-main">
        <section className="stocks-panel">
          <div className="panel-header">
            <h2>Stocks</h2>
            <button onClick={fetchStocks} disabled={loadingStocks}>
              {loadingStocks ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>
          {error && <div className="error">{error}</div>}
          {stocks.length === 0 && !loadingStocks && (
            <p className="empty">No stocks yet. Try commands like "add AAPL Apple 195.3" in the chatbot.</p>
          )}
          <table className="stocks-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Price</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {[...stocks]
                .sort((a, b) => a.symbol.localeCompare(b.symbol))
                .map((s) => (
                <tr key={s.symbol}>
                  <td>{s.symbol}</td>
                  <td>{s.name}</td>
                  <td>{s.price}</td>
                  <td>{s.notes ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="chat-panel">
          <h2>Chatbot</h2>
          <div className="chat-help">
            <p>Try commands like:</p>
            <ul>
              <li><code>list</code></li>
              <li><code>add AAPL Apple 195.3</code></li>
              <li><code>update AAPL 200.0</code></li>
              <li><code>remove AAPL</code></li>
            </ul>
          </div>
          <div className="chat-history">
            {chatHistory.map((line, idx) => (
              <div key={idx} className={line.startsWith('You:') ? 'chat-line user' : 'chat-line bot'}>
                {line}
              </div>
            ))}
          </div>
          <div className="chat-input-row">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a command and press Enter…"
              rows={3}
            />
            <button onClick={handleSendChat} disabled={chatLoading}>
              {chatLoading ? 'Sending…' : 'Send'}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};
