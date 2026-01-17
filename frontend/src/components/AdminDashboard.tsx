import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  AreaChart, Area
} from 'recharts';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Activity, DollarSign, Zap, TrendingUp, Youtube, Globe, Instagram, Clock } from 'lucide-react';

interface AdminStats {
  llm: {
    summary: {
      total_calls: number;
      total_input_tokens: number;
      total_output_tokens: number;
      total_tokens: number;
      total_cost_usd: number;
      average_cost_per_call: number;
      average_tokens_per_call: number;
    };
    recent_calls: Array<{
      timestamp: string;
      model: string;
      input_tokens: number;
      output_tokens: number;
      cost_usd: number;
    }>;
  };
  recipes: {
    total: number;
    by_source: {
      youtube: number;
      instagram: number;
      tiktok: number;
      facebook: number;
      web: number;
      unknown: number;
    };
    by_category: Array<{
      category: string;
      count: number;
    }>;
  };
  recent_activity: Array<{
    id: number;
    name: string;
    source_type: string;
    created_at: string;
  }>;
}

const SOURCE_COLORS: Record<string, string> = {
  youtube: '#FF0000',
  instagram: '#E1306C',
  tiktok: '#000000',
  facebook: '#1877F2',
  web: '#10B981',
  unknown: '#6B7280'
};

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  youtube: <Youtube size={16} className="text-red-500" />,
  instagram: <Instagram size={16} className="text-pink-500" />,
  tiktok: <span className="text-xs font-bold">TT</span>,
  facebook: <span className="text-blue-600 font-bold text-xs">FB</span>,
  web: <Globe size={16} className="text-green-500" />,
  unknown: <Globe size={16} className="text-gray-500" />
};

const fetchAdminStats = async (): Promise<AdminStats> => {
  const response = await axios.get('/api/v1/admin/stats');
  return response.data;
};

const formatCost = (cost: number): string => {
  if (cost < 0.01) {
    return `$${cost.toFixed(6)}`;
  }
  return `$${cost.toFixed(4)}`;
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toString();
};

const StatCard = ({ title, value, subtitle, icon: Icon, color = "blue" }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
  color?: string;
}) => (
  <Card className="bg-card">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900/30`}>
          <Icon className={`text-${color}-600 dark:text-${color}-400`} size={24} />
        </div>
      </div>
    </CardContent>
  </Card>
);

const AdminDashboard = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['adminStats'],
    queryFn: fetchAdminStats,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-destructive p-8">
        Failed to load admin statistics. Make sure the backend is running.
      </div>
    );
  }

  if (!stats) return null;

  const sourceData = Object.entries(stats.recipes.by_source)
    .filter(([_, count]) => count > 0)
    .map(([source, count]) => ({
      name: source.charAt(0).toUpperCase() + source.slice(1),
      value: count,
      color: SOURCE_COLORS[source] || '#6B7280'
    }));

  const tokenData = stats.llm.recent_calls.slice().reverse().map((call, index) => ({
    name: `Call ${index + 1}`,
    input: call.input_tokens,
    output: call.output_tokens,
    cost: call.cost_usd * 1000
  }));

  const hasLLMData = stats.llm.summary.total_calls > 0;
  const hasRecipeData = stats.recipes.total > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl md:text-3xl font-bold">Admin Dashboard</h1>
        <span className="text-sm text-muted-foreground">
          Auto-refreshes every 30s
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Recipes"
          value={stats.recipes.total}
          subtitle="Across all sources"
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="LLM Calls"
          value={stats.llm.summary.total_calls}
          subtitle={hasLLMData ? `Avg ${formatNumber(stats.llm.summary.average_tokens_per_call)} tokens/call` : 'No calls yet'}
          icon={Zap}
          color="purple"
        />
        <StatCard
          title="Total Tokens"
          value={formatNumber(stats.llm.summary.total_tokens)}
          subtitle={`${formatNumber(stats.llm.summary.total_input_tokens)} in / ${formatNumber(stats.llm.summary.total_output_tokens)} out`}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Estimated Cost"
          value={formatCost(stats.llm.summary.total_cost_usd)}
          subtitle={hasLLMData ? `Avg ${formatCost(stats.llm.summary.average_cost_per_call)}/call` : 'No costs yet'}
          icon={DollarSign}
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recipes by Source</CardTitle>
          </CardHeader>
          <CardContent>
            {hasRecipeData ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sourceData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {sourceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No recipes imported yet
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Source Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.recipes.by_source).map(([source, count]) => {
                const percentage = stats.recipes.total > 0 
                  ? ((count / stats.recipes.total) * 100).toFixed(1) 
                  : '0';
                return (
                  <div key={source} className="flex items-center gap-3">
                    <div className="w-8 flex justify-center">
                      {SOURCE_ICONS[source]}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium capitalize">{source}</span>
                        <span className="text-sm text-muted-foreground">{count} ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div 
                          className="h-2 rounded-full transition-all"
                          style={{ 
                            width: `${percentage}%`,
                            backgroundColor: SOURCE_COLORS[source]
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Token Usage (Recent Calls)</CardTitle>
          </CardHeader>
          <CardContent>
            {hasLLMData && tokenData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={tokenData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="input" 
                      stackId="1"
                      stroke="#3B82F6" 
                      fill="#3B82F6" 
                      fillOpacity={0.6}
                      name="Input Tokens"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="output" 
                      stackId="1"
                      stroke="#10B981" 
                      fill="#10B981" 
                      fillOpacity={0.6}
                      name="Output Tokens"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No LLM calls recorded yet. Import a recipe to see usage data.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recipes.by_category.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.recipes.by_category} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis 
                      dataKey="category" 
                      type="category" 
                      width={100}
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="count" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No categories yet
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {stats.recent_activity.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_activity.map((recipe) => (
                <div key={recipe.id} className="flex items-center gap-3 p-3 bg-secondary/50 rounded-lg">
                  <div className="w-8 flex justify-center">
                    {SOURCE_ICONS[recipe.source_type] || SOURCE_ICONS.unknown}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{recipe.name}</p>
                    <p className="text-xs text-muted-foreground capitalize">
                      {recipe.source_type || 'Unknown source'}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock size={12} />
                    {recipe.created_at 
                      ? new Date(recipe.created_at).toLocaleDateString()
                      : 'Unknown date'
                    }
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No recent activity
            </div>
          )}
        </CardContent>
      </Card>

      {hasLLMData && stats.llm.recent_calls.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent LLM Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 px-3 font-medium">Time</th>
                    <th className="text-left py-2 px-3 font-medium">Model</th>
                    <th className="text-right py-2 px-3 font-medium">Input</th>
                    <th className="text-right py-2 px-3 font-medium">Output</th>
                    <th className="text-right py-2 px-3 font-medium">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.llm.recent_calls.slice(0, 10).map((call, index) => (
                    <tr key={index} className="border-b border-border/50">
                      <td className="py-2 px-3 text-muted-foreground">
                        {new Date(call.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-2 px-3 font-mono text-xs">{call.model}</td>
                      <td className="py-2 px-3 text-right">{formatNumber(call.input_tokens)}</td>
                      <td className="py-2 px-3 text-right">{formatNumber(call.output_tokens)}</td>
                      <td className="py-2 px-3 text-right font-mono">{formatCost(call.cost_usd)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminDashboard;
