import { useState } from 'react';
import ChakraForm from './components/ChakraForm';
import { LayoutDashboard, Target, Share2, Sparkles, Download, Calendar } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [results, setResults] = useState<any>(null);

  // Explicitly ensuring the backend port matches your Uvicorn instance
  const backendUrl = "http://localhost:8000";

  return (
    <div className="flex min-h-screen bg-[#050505] text-slate-200 font-sans">
      {/* Sidebar Navigation */}
      <nav className="w-72 bg-[#0a0a0a] border-r border-white/5 p-8 hidden md:block">
        <div className="flex items-center gap-2 mb-12">
          <div className="bg-emerald-500 p-2 rounded-lg"><Sparkles size={24} className="text-black" /></div>
          <h1 className="text-xl font-black italic tracking-tighter">SATH-CHAKRA <span className="text-emerald-500">AI</span></h1>
        </div>
        <ul className="space-y-4">
          <li onClick={() => setActiveTab('dashboard')} className={`flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition ${activeTab === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500 hover:text-white'}`}>
            <LayoutDashboard size={20}/> Dashboard
          </li>
          <li onClick={() => setActiveTab('roadmap')} className={`flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition ${activeTab === 'roadmap' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500 hover:text-white'}`}>
            <Target size={20}/> 2026 Roadmap
          </li>
          <li onClick={() => setActiveTab('share')} className={`flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition ${activeTab === 'share' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500 hover:text-white'}`}>
            <Share2 size={20}/> Share Card
          </li>
        </ul>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-12 overflow-y-auto">
        {activeTab === 'dashboard' && (
          <ChakraForm onResultsReady={(data) => {
            setResults(data);
            // Optionally auto-switch to roadmap upon success
          }} />
        )}

        {activeTab === 'roadmap' && (
          <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
            <h2 className="text-3xl font-black uppercase italic tracking-tighter">Strategic Roadmap</h2>
            {results ? (
              <>
                {/* Download link for .ics file */}
                <a
                  href={`${backendUrl}${results.calendar_url}`}
                  download
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 bg-white/5 p-6 rounded-3xl border border-white/5 hover:bg-white/10 transition group"
                >
                  <Calendar className="text-emerald-500 group-hover:scale-110 transition" />
                  <div>
                    <p className="text-xs font-bold text-emerald-500 uppercase">Sync Neural Roadmap</p>
                    <p className="text-sm text-slate-400">Download .ics file for Calendar integration</p>
                  </div>
                </a>
                <div className="bg-[#0a0a0a] p-10 rounded-[2.5rem] border border-white/5 text-slate-300 shadow-2xl">
                  <pre className="whitespace-pre-wrap font-sans leading-relaxed">{results.ai_analysis}</pre>
                </div>
              </>
            ) : (
              <div className="text-center py-20 opacity-30 italic">Initialize your strategy in the Dashboard to view your roadmap...</div>
            )}
          </div>
        )}

        {activeTab === 'share' && (
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in duration-500">
            <h2 className="text-3xl font-black uppercase italic tracking-tighter">Shareable Identity Card</h2>
            {results ? (
              <>
                <div className="bg-black p-4 rounded-[3rem] border border-white/10 shadow-[0_0_50px_-12px_rgba(16,185,129,0.2)] inline-block">
                  <img src={`${backendUrl}${results.shareable_card_url}`} alt="Card" className="max-w-full rounded-[2rem] border border-white/5" />
                </div>
                <div className="flex justify-center">
                  <a
                    href={`${backendUrl}${results.shareable_card_url}`}
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-3 bg-emerald-600 hover:bg-emerald-500 text-white font-black px-12 py-5 rounded-2xl shadow-xl shadow-emerald-900/20 transition-all uppercase tracking-widest text-xs"
                  >
                    <Download size={18}/> Download High-Res Card
                  </a>
                </div>
              </>
            ) : (
              <div className="text-center py-20 opacity-30 italic">Generate your card in the Dashboard first...</div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}