import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

interface Props {
  current: Record<string, number>;
  target: Record<string, number>;
}

export default function ChakraChart({ current, target }: Props) {
  // Mapping technical keys to readable labels for the axis
  const data = Object.keys(current).map(key => ({
    subject: key.replace(/_/g, ' ').toUpperCase(),
    A: current[key],
    B: target[key],
    fullMark: 10,
  }));

  return (
    <div className="w-full h-[400px] bg-black/20 rounded-[2rem] p-4 border border-white/5">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
          <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
          <Radar
            name="Current Status"
            dataKey="A"
            stroke="#94a3b8"
            fill="#94a3b8"
            fillOpacity={0.3}
          />
          <Radar
            name="2026 Target"
            dataKey="B"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.5}
          />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}