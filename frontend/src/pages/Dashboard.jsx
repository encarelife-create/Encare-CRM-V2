import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Users,
  AlertTriangle,
  TrendingUp,
  Phone,
  Pill,
  FlaskConical,
  ShoppingBag,
  Activity,
  ChevronRight,
  RefreshCw,
  IndianRupee,
  FileText,
  UserCheck,
  Clock
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { getDashboardStats, getPatientsToCall, seedDatabase, generateOpportunities, getRevenueSummary } from "@/lib/api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [patientsToCall, setPatientsToCall] = useState([]);
  const [revenueSummary, setRevenueSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [callFilter, setCallFilter] = useState("all");

  const fetchData = async () => {
    try {
      const [statsRes, patientsRes, revRes] = await Promise.all([
        getDashboardStats(),
        getPatientsToCall(),
        getRevenueSummary()
      ]);
      setStats(statsRes.data);
      setPatientsToCall(patientsRes.data);
      setRevenueSummary(revRes.data);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      if (error.response?.status === 500 || !stats) {
        setStats({
          total_patients: 0,
          high_priority_patients: 0,
          opportunities: { refills: 0, lab_tests: 0, products: 0, invoices: 0, adherence: 0 },
          expected_revenue: 0,
          total_monthly_invoice: 0,
          today_tasks: [],
          disease_distribution: []
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedDatabase = async () => {
    setSeeding(true);
    try {
      await seedDatabase();
      toast.success("Database seeded with sample patients!");
      await fetchData();
    } catch (error) {
      toast.error("Failed to seed database");
    } finally {
      setSeeding(false);
    }
  };

  const handleRefreshOpportunities = async () => {
    try {
      await generateOpportunities();
      toast.success("Opportunities refreshed!");
      await fetchData();
    } catch (error) {
      toast.error("Failed to refresh opportunities");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    );
  }

  const quickStats = [
    {
      label: "Total Patients",
      value: stats?.total_patients || 0,
      icon: Users,
      color: "bg-blue-50 text-blue-500",
      link: "/patients"
    },
    {
      label: "High Priority",
      value: stats?.high_priority_patients || 0,
      icon: AlertTriangle,
      color: "bg-red-50 text-red-500",
      link: "/patients?priority=high"
    }
  ];

  // Current month label for revenue section
  const monthLabel = revenueSummary?.month
    ? new Date(revenueSummary.month + "-01").toLocaleDateString("en-IN", { month: "long", year: "numeric" })
    : new Date().toLocaleDateString("en-IN", { month: "long", year: "numeric" });
  const expectedTotal = revenueSummary?.expected?.total || 0;
  const convertedTotal = revenueSummary?.converted?.total || 0;
  const conversionRate = revenueSummary?.conversion_rate || 0;
  const expectedInvoice = revenueSummary?.expected?.invoice_followup || 0;
  const expectedLab = revenueSummary?.expected?.lab_test || 0;
  const convertedInvoice = revenueSummary?.converted?.invoice_followup || 0;
  const convertedLab = revenueSummary?.converted?.lab_test || 0;

  const opportunityCards = [
    { type: "refill", label: "Medicine Refills", icon: Pill, count: stats?.opportunities?.refills || 0, color: "text-red-500 bg-red-50" },
    { type: "lab_test", label: "Lab Tests Due", icon: FlaskConical, count: stats?.opportunities?.lab_tests || 0, color: "text-purple-500 bg-purple-50" },
    { type: "product", label: "Product Suggestions", icon: ShoppingBag, count: stats?.opportunities?.products || 0, color: "text-orange-500 bg-orange-50" },
    { type: "invoice", label: "Invoice Follow-ups", icon: FileText, count: stats?.opportunities?.invoices || 0, color: "text-teal-500 bg-teal-50" },
    { type: "adherence", label: "Adherence Alerts", icon: UserCheck, count: stats?.opportunities?.adherence || 0, color: "text-emerald-500 bg-emerald-50" }
  ];

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-teal-500 to-emerald-400 rounded-xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold font-['Manrope']">Good Morning, Healthcare Assistant!</h1>
            <p className="text-white/80 mt-1">
              You have <span className="font-semibold">{patientsToCall.filter(e => e.status !== 'completed').length} tasks</span> remaining today
            </p>
          </div>
          <div className="flex gap-2">
            {stats?.total_patients === 0 && (
              <Button
                onClick={handleSeedDatabase}
                disabled={seeding}
                className="bg-white text-coral-500 hover:bg-white/90"
                data-testid="seed-database-btn"
              >
                {seeding ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : null}
                Load Sample Data
              </Button>
            )}
            <Button
              onClick={handleRefreshOpportunities}
              variant="outline"
              className="border-white/30 text-white hover:bg-white/20"
              data-testid="refresh-opportunities-btn"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-4">
        {quickStats.map((stat, i) => (
          <Link to={stat.link} key={i}>
            <Card className="card-hover cursor-pointer" data-testid={`stat-${stat.label.toLowerCase().replace(/ /g, '-')}`}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-xl ${stat.color}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900 tabular-nums">{stat.value}</p>
                    <p className="text-xs text-slate-500">{stat.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Revenue — Expected vs Converted (Monthly) */}
      <div data-testid="revenue-section">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-slate-900 font-['Manrope']">
            Revenue <span className="text-slate-400 font-normal text-sm">• {monthLabel}</span>
          </h2>
          <Badge variant="outline" className={`${conversionRate >= 50 ? 'bg-green-50 text-green-700 border-green-200' : conversionRate >= 20 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`} data-testid="conversion-rate-badge">
            {conversionRate}% converted
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Expected Revenue KPI */}
          <Link to="/opportunities">
            <Card className="card-hover cursor-pointer border-l-4 border-l-teal-400" data-testid="revenue-expected-card">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-teal-50 text-teal-500">
                      <TrendingUp className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Revenue Opportunities</p>
                      <p className="text-2xl font-bold text-slate-900 tabular-nums" data-testid="expected-total">
                        ₹{expectedTotal.toLocaleString('en-IN')}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">from pending opportunities</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <p className="text-slate-500">Invoice Follow-up</p>
                    <p className="font-semibold text-slate-800 tabular-nums" data-testid="expected-invoice-followup">
                      ₹{expectedInvoice.toLocaleString('en-IN')}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Lab Tests</p>
                    <p className="font-semibold text-slate-800 tabular-nums" data-testid="expected-lab-test">
                      ₹{expectedLab.toLocaleString('en-IN')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Converted Revenue KPI */}
          <Card className="card-hover border-l-4 border-l-green-500" data-testid="revenue-converted-card">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-green-50 text-green-600">
                    <IndianRupee className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Converted Revenue</p>
                    <p className="text-2xl font-bold text-green-700 tabular-nums" data-testid="converted-total">
                      ₹{convertedTotal.toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">from bookings & invoices</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <p className="text-slate-500">Invoice Follow-up</p>
                  <p className="font-semibold text-slate-800 tabular-nums" data-testid="converted-invoice-followup">
                    ₹{convertedInvoice.toLocaleString('en-IN')}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Lab Tests</p>
                  <p className="font-semibold text-slate-800 tabular-nums" data-testid="converted-lab-test">
                    ₹{convertedLab.toLocaleString('en-IN')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-3 font-['Manrope']">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {opportunityCards.map((card, i) => (
            <Link to={`/opportunities?type=${card.type}`} key={i}>
              <Card className="quick-action-card cursor-pointer hover:shadow-md" data-testid={`quick-action-${card.type}`}>
                <CardContent className="p-4 text-center">
                  <div className={`w-14 h-14 mx-auto rounded-xl ${card.color} flex items-center justify-center mb-3`}>
                    <card.icon className="h-7 w-7" />
                  </div>
                  <p className="text-2xl font-bold text-slate-900 tabular-nums">{card.count}</p>
                  <p className="text-xs text-slate-500 mt-1">{card.label}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Patients to Call Today */}
        <Card data-testid="patients-to-call-card" className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold font-['Manrope']">Daily Task List</CardTitle>
              <Link to="/opportunities">
                <Button variant="ghost" size="sm" className="text-teal-600" data-testid="view-all-patients-btn">
                  View All <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </Link>
            </div>
            <div className="flex flex-wrap gap-2 mt-3" data-testid="task-filters">
              {[
                { key: "all", label: "All" },
                { key: "pending", label: "Pending" },
                { key: "completed", label: "Completed" },
                { key: "upcoming", label: "Upcoming" },
                { key: "overdue", label: "Overdue" },
                { key: "no_contact", label: "30-day Follow-up" },
                { key: "feedback_call", label: "Feedback" },
              ].map(f => (
                <Button
                  key={f.key}
                  variant={callFilter === f.key ? "default" : "outline"}
                  size="sm"
                  className={callFilter === f.key ? "gradient-teal text-white" : "text-slate-600"}
                  onClick={() => setCallFilter(f.key)}
                  data-testid={`filter-${f.key}`}
                >
                  {f.label}
                  <span className="ml-1.5 text-xs opacity-80">
                    {f.key === "all" ? patientsToCall.length
                      : f.key === "no_contact" ? patientsToCall.filter(e => e.task_type === "no_contact").length
                      : f.key === "feedback_call" ? patientsToCall.filter(e => e.task_type === "feedback_call").length
                      : patientsToCall.filter(e => e.status === f.key).length}
                  </span>
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {(() => {
              const filtered = callFilter === "all" ? patientsToCall
                : callFilter === "no_contact" ? patientsToCall.filter(e => e.task_type === "no_contact")
                : callFilter === "feedback_call" ? patientsToCall.filter(e => e.task_type === "feedback_call")
                : patientsToCall.filter(e => e.status === callFilter);
              if (filtered.length === 0) {
                return (
                  <div className="text-center py-8 text-slate-500">
                    <Phone className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                    <p>No tasks in this category</p>
                  </div>
                );
              }
              const statusConfig = {
                pending: { color: "bg-amber-100 text-amber-700 border-amber-200", dot: "bg-amber-500" },
                completed: { color: "bg-green-100 text-green-700 border-green-200", dot: "bg-green-500" },
                upcoming: { color: "bg-blue-100 text-blue-700 border-blue-200", dot: "bg-blue-500" },
                overdue: { color: "bg-red-100 text-red-700 border-red-200", dot: "bg-red-500" },
              };
              return (
                <div className="grid md:grid-cols-2 gap-2">
                  {filtered.slice(0, 20).map((entry, i) => {
                    const sc = statusConfig[entry.status] || statusConfig.pending;
                    return (
                      <Link to={`/patients/${entry.patient_id}`} key={entry.id || i}>
                        <div className={`flex items-center justify-between p-3 rounded-lg border hover:shadow-sm transition-all ${entry.status === 'completed' ? 'bg-slate-50/60 opacity-75' : 'bg-white'}`} data-testid={`task-entry-${i}`}>
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="relative flex-shrink-0">
                              <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-medium
                                ${entry.priority === 'high' ? 'bg-red-500' : entry.priority === 'medium' ? 'bg-orange-500' : 'bg-green-500'}`}>
                                {entry.patient_name.charAt(0)}
                              </div>
                              <span className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white ${sc.dot}`} />
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium text-sm text-slate-900 truncate">{entry.patient_name}</p>
                              <p className="text-xs text-slate-500 truncate">{entry.description}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                            {entry.follow_up_time && (
                              <span className="text-xs font-medium text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded whitespace-nowrap" data-testid={`entry-time-${i}`}>
                                <Clock className="h-3 w-3 inline mr-0.5" />{entry.follow_up_time}
                              </span>
                            )}
                            <Badge variant="outline" className={`text-[10px] px-1.5 py-0 capitalize whitespace-nowrap ${sc.color}`} data-testid={`entry-status-${i}`}>
                              {entry.status}
                            </Badge>
                          </div>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              );
            })()}
          </CardContent>
        </Card>

        {/* Disease Distribution */}
        <Card data-testid="disease-distribution-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold font-['Manrope']">Patient Health Conditions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats?.disease_distribution?.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Activity className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                <p>No patient data yet</p>
              </div>
            ) : (
              stats?.disease_distribution?.slice(0, 6).map((item, i) => {
                const percentage = stats.total_patients > 0
                  ? Math.round((item.count / stats.total_patients) * 100)
                  : 0;
                const colors = ['bg-red-500', 'bg-purple-500', 'bg-orange-500', 'bg-blue-500', 'bg-green-500', 'bg-pink-500'];
                return (
                  <div key={i} data-testid={`disease-item-${i}`}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-slate-700">{item.disease}</span>
                      <span className="text-slate-500 tabular-nums">{item.count} patients ({percentage}%)</span>
                    </div>
                    <Progress value={percentage} className="h-2" indicatorClassName={colors[i % colors.length]} />
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      {/* Today's Revenue Opportunities */}
      <Card data-testid="revenue-opportunities-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold font-['Manrope'] flex items-center gap-2">
              <IndianRupee className="h-5 w-5 text-green-500" />
              Revenue Opportunities
            </CardTitle>
            <div className="text-right">
              <p className="text-2xl font-bold text-green-600 tabular-nums">
                ₹{(stats?.expected_revenue || 0).toLocaleString('en-IN')}
              </p>
              <p className="text-xs text-slate-500">Expected Today</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {opportunityCards.map((card, i) => (
              <div key={i} className="text-center p-4 rounded-lg bg-slate-50" data-testid={`revenue-opp-${card.type}`}>
                <card.icon className={`h-6 w-6 mx-auto mb-2 ${card.color.split(' ')[0]}`} />
                <p className="text-lg font-bold text-slate-900 tabular-nums">{card.count}</p>
                <p className="text-xs text-slate-500">{card.label}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
