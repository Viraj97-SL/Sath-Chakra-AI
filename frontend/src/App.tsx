import { useState } from 'react';
import ChakraForm from './components/ChakraForm';
import { LayoutDashboard, Target, Share2, Sparkles, Download, Calendar } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [results, setResults] = useState<any>(null);

  const backendUrl = "https://sath-chakra-ai-production.up.railway.app";

  const handleDownload = async (imageUrl: string) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Sath-Chakra-Identity.png');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      window.open(imageUrl, '_blank');
    }
  };

  return (
    <div className="flex min-h-screen bg-[#050505] text-slate-200 font-sans">
      {/* Sidebar Navigation - Hidden on mobile */}
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

      {/* Main Content Area - Responsive padding added */}
      <main className="flex-1 p-6 md:p-12 pb-24 md:pb-12 overflow-y-auto">
        {/* Mobile Header Branding */}
        <div className="flex items-center gap-2 mb-8 md:hidden justify-center">
           <Sparkles size={20} className="text-emerald-500" />
           <h1 className="text-lg font-black italic tracking-tighter uppercase">Sath-Chakra AI</h1>
        </div>

        {activeTab === 'dashboard' && (
          <ChakraForm onResultsReady={(data) => setResults(data)} />
        )}

        {activeTab === 'roadmap' && (
          <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
            <h2 className="text-2xl md:text-3xl font-black uppercase italic tracking-tighter text-center md:text-left">Strategic Roadmap</h2>
            {results ? (
              <>
                <a
                  href={`${backendUrl}${results.calendar_url}`}
                  className="flex items-center gap-4 bg-white/5 p-4 md:p-6 rounded-3xl border border-white/5 hover:bg-white/10 transition group"
                >
                  <Calendar className="text-emerald-500 group-hover:scale-110 transition shrink-0" />
                  <div>
                    <p className="text-[10px] md:text-xs font-bold text-emerald-500 uppercase">Sync Neural Roadmap</p>
                    <p className="text-xs md:text-sm text-slate-400">Download .ics file for Calendar integration</p>
                  </div>
                </a>

                <div className="bg-[#0a0a0a] p-6 md:p-10 rounded-[2rem] md:rounded-[2.5rem] border border-white/5 text-slate-300 shadow-2xl max-h-[60vh] md:max-h-[70vh] overflow-y-auto custom-scrollbar">
                  <pre className="whitespace-pre-wrap font-sans leading-relaxed text-base md:text-lg">
                    {results.ai_analysis}
                  </pre>
                </div>
              </>
            ) : (
              <div className="text-center py-20 opacity-30 italic">Initialize your strategy in the Dashboard...</div>
            )}
          </div>
        )}

        {activeTab === 'share' && (
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in duration-500">
            <h2 className="text-2xl md:text-3xl font-black uppercase italic tracking-tighter">Shareable Identity Card</h2>
            {results ? (
              <>
                <div className="bg-black p-2 md:p-4 rounded-[2rem] md:rounded-[3rem] border border-white/10 shadow-[0_0_50px_-12px_rgba(16,185,129,0.2)] inline-block">
                  <img
                    src={`${backendUrl}${results.shareable_card_url}`}
                    alt="Card"
                    className="w-full max-w-sm md:max-w-full rounded-[1.5rem] md:rounded-[2rem] border border-white/5"
                  />
                </div>
                <div className="flex justify-center">
                  <button
                    onClick={() => handleDownload(`${backendUrl}${results.shareable_card_url}`)}
                    className="inline-flex items-center gap-3 bg-emerald-600 hover:bg-emerald-500 text-white font-black px-8 md:px-12 py-4 md:py-5 rounded-2xl shadow-xl transition-all uppercase tracking-widest text-[10px] md:text-xs"
                  >
                    <Download size={18}/> Download High-Res Card
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-20 opacity-30 italic">Generate your card in the Dashboard first...</div>
            )}
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation - Visible only on small screens */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0a0a0a]/90 backdrop-blur-xl border-t border-white/5 p-4 flex justify-around items-center md:hidden z-50">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`flex flex-col items-center gap-1 transition ${activeTab === 'dashboard' ? 'text-emerald-400' : 'text-slate-500'}`}
        >
          <LayoutDashboard size={20} />
          <span className="text-[9px] uppercase font-bold tracking-widest">Dash</span>
        </button>

        <button
          onClick={() => setActiveTab('roadmap')}
          className={`flex flex-col items-center gap-1 transition ${activeTab === 'roadmap' ? 'text-emerald-400' : 'text-slate-500'}`}
        >
          <Target size={20} />
          <span className="text-[9px] uppercase font-bold tracking-widest">Roadmap</span>
        </button>

        <button
          onClick={() => setActiveTab('share')}
          className={`flex flex-col items-center gap-1 transition ${activeTab === 'share' ? 'text-emerald-400' : 'text-slate-500'}`}
        >
          <Share2 size={20} />
          <span className="text-[9px] uppercase font-bold tracking-widest">Card</span>
        </button>
      </div>
    </div>
  );
}