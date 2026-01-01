import { useState } from 'react';
import api from '../api';
import { Rocket, Brain, Activity } from 'lucide-react';
import ChakraChart from './ChakraChart';

const dimensions = [
  'career_finance', 'health_fitness', 'relationships_family',
  'spirituality_inner_peace', 'personal_growth_learning',
  'fun_recreation', 'physical_environment', 'contribution_legacy'
];

export default function ChakraForm({ onResultsReady }: { onResultsReady: (data: any) => void }) {
  const [loading, setLoading] = useState(false);
  const [localResults, setLocalResults] = useState<any>(null);

  const [formData, setFormData] = useState({
    user_id: "user_" + Math.random().toString(36).substr(2, 9),
    email: "",
    age: 25,
    job_status: "employed",
    current_status: dimensions.reduce((acc, d) => ({...acc, [d]: 5}), {}),
    ideal_identity: dimensions.reduce((acc, d) => ({...acc, [d]: 9}), {}),
    language: "sinhala"
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await api.post('/analyze-chakra', formData);
      setLocalResults(response.data);
      onResultsReady(response.data);
    } catch (err) {
      alert("Synchronization Error: Check backend status.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-12 px-6 space-y-12">
      <div className="bg-[#0a0a0a]/60 backdrop-blur-3xl border border-white/5 p-12 rounded-[3rem] shadow-2xl">
        <header className="text-center mb-16">
          <div className="inline-flex items-center justify-center p-4 bg-emerald-500/10 rounded-2xl mb-6 border border-emerald-500/20">
            <Brain className="text-emerald-400" size={32} />
          </div>
          <h2 className="text-4xl font-black text-white tracking-tighter mb-4 uppercase italic">Sath-Chakra <span className="text-emerald-500">AI</span></h2>
          <p className="text-slate-500 max-w-lg mx-auto leading-relaxed text-sm">Synchronize your current reality with your 2026 ideal identity.</p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-12">
          {/* Identity Inputs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-emerald-500/70 ml-2">Email Identifier</label>
              <input required type="email" placeholder="EMAIL..." className="w-full bg-black/40 border border-white/10 p-4 rounded-2xl text-white outline-none focus:border-emerald-500 transition-all font-mono" onChange={(e) => setFormData({...formData, email: e.target.value})} />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-emerald-500/70 ml-2">Current Age</label>
              <input required type="number" placeholder="25" className="w-full bg-black/40 border border-white/10 p-4 rounded-2xl text-white outline-none focus:border-emerald-500 transition-all font-mono" onChange={(e) => setFormData({...formData, age: parseInt(e.target.value)})} />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-emerald-500/70 ml-2">Job Status</label>
              <select className="w-full bg-black/40 border border-white/10 p-4 rounded-2xl text-white outline-none focus:border-emerald-500 transition-all font-mono appearance-none" onChange={(e) => setFormData({...formData, job_status: e.target.value})}>
                <option value="employed">Employed</option>
                <option value="student">Student</option>
                <option value="self-employed">Self-Employed</option>
                <option value="unemployed">Unemployed</option>
                <option value="freelance">Freelance</option>
              </select>
            </div>
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {dimensions.map((d) => (
              <div key={d} className="bg-white/5 p-8 rounded-[2.5rem] border border-white/5 hover:border-emerald-500/20 transition-all group">
                <div className="flex items-center gap-3 mb-8">
                  <Activity size={16} className="text-emerald-500" />
                  <h4 className="text-[11px] font-black uppercase tracking-widest text-slate-300">{d.replace(/_/g, ' ')}</h4>
                </div>
                <div className="space-y-8">
                  <div>
                    <div className="flex justify-between text-[9px] font-bold text-slate-500 mb-2 uppercase"><span>Current Reality</span><span>LVL {(formData.current_status as any)[d]}</span></div>
                    <input type="range" min="1" max="10" value={(formData.current_status as any)[d]} className="w-full accent-slate-400 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer" onChange={(e) => setFormData({...formData, current_status: {...formData.current_status, [d]: parseInt(e.target.value)}})} />
                  </div>
                  <div>
                    <div className="flex justify-between text-[9px] font-bold text-emerald-500 mb-2 uppercase"><span>2026 Target</span><span>LVL {(formData.ideal_identity as any)[d]}</span></div>
                    <input type="range" min="1" max="10" value={(formData.ideal_identity as any)[d]} className="w-full accent-emerald-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer" onChange={(e) => setFormData({...formData, ideal_identity: {...formData.ideal_identity, [d]: parseInt(e.target.value)}})} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button type="submit" disabled={loading} className="w-full bg-emerald-600 py-8 rounded-3xl font-black text-white uppercase tracking-[0.3em] hover:bg-emerald-500 transition-all flex items-center justify-center gap-4 shadow-2xl shadow-emerald-900/20">
            {loading ? <span className="animate-pulse">Synchronizing Neural Data...</span> : <><Rocket size={20} /> Initialize 2026 Strategy</>}
          </button>
        </form>
      </div>

      {localResults && (
        <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="bg-[#0a0a0a]/40 backdrop-blur-xl rounded-[3rem] border border-white/5 p-12 shadow-2xl">
            <h4 className="text-emerald-500 font-bold mb-8 uppercase text-[10px] tracking-[0.4em] text-center">Visual Gap Analysis</h4>
            <ChakraChart current={formData.current_status} target={formData.ideal_identity} />
          </div>
          <div className="bg-emerald-500/10 border border-emerald-500/20 p-10 rounded-[2.5rem] text-center">
            <h3 className="text-2xl font-black text-white mb-2 uppercase italic tracking-tighter">Neural Strategy Ready</h3>
            <p className="text-slate-400 text-sm">Visit the Roadmap and Share Card tabs for full downloads.</p>
          </div>
        </div>
      )}
    </div>
  );
}