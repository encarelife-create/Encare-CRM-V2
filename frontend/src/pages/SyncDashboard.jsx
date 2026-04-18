import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  RefreshCw, Download, CheckCircle2, AlertCircle, Clock,
  User, Pill, Activity, ArrowRight
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  listEncarePatientsForSync,
  syncPatient,
  syncMedications,
  syncVitals,
  getSyncStatus
} from "@/lib/api";

export default function SyncDashboard() {
  const [encarePatients, setEncarePatients] = useState([]);
  const [syncLogs, setSyncLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [pRes, sRes] = await Promise.all([
        listEncarePatientsForSync(),
        getSyncStatus()
      ]);
      setEncarePatients(pRes.data);
      setSyncLogs(sRes.data);
    } catch {
      toast.error("Failed to load sync data");
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (encareId, type) => {
    setSyncing(prev => ({ ...prev, [`${encareId}-${type}`]: true }));
    try {
      if (type === "patient") {
        const res = await syncPatient(encareId);
        toast.success(`Patient ${res.data.action}: ${res.data.medicines_synced} medicines synced`);
      } else if (type === "medications") {
        const res = await syncMedications(encareId);
        toast.success(`${res.data.medicines_synced} medications synced`);
      } else if (type === "vitals") {
        const res = await syncVitals(encareId);
        const c = res.data.counts;
        toast.success(`Vitals synced: ${c.blood_glucose} glucose, ${c.blood_pressure} BP readings`);
      }
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || `Sync failed for ${type}`);
    } finally {
      setSyncing(prev => ({ ...prev, [`${encareId}-${type}`]: false }));
    }
  };

  const handleSyncAll = async (encareId) => {
    setSyncing(prev => ({ ...prev, [`${encareId}-all`]: true }));
    try {
      await syncPatient(encareId);
      try { await syncVitals(encareId); } catch {}
      toast.success("Full sync complete!");
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Sync failed");
    } finally {
      setSyncing(prev => ({ ...prev, [`${encareId}-all`]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="sync-loading">
        <RefreshCw className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="sync-dashboard-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-['Manrope']">
            enCARE Sync
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Import and sync patient data from enCARE MEDI REMINDER
          </p>
        </div>
        <Button variant="outline" onClick={fetchData} data-testid="refresh-sync-btn">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Available enCARE Patients */}
      <Card data-testid="encare-patients-card">
        <CardHeader>
          <CardTitle className="text-lg font-['Manrope'] flex items-center gap-2">
            <Download className="h-5 w-5 text-teal-500" />
            Available enCARE Patients
          </CardTitle>
          <p className="text-sm text-slate-500">
            These patients exist in the enCARE system and can be synced to this CRM
          </p>
        </CardHeader>
        <CardContent>
          {encarePatients.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No patients available for sync</p>
          ) : (
            <div className="space-y-3">
              {encarePatients.map((ep) => (
                <div
                  key={ep.encare_user_id}
                  className={`p-4 rounded-lg border transition-colors ${
                    ep.already_synced ? 'border-green-200 bg-green-50/50' : 'border-slate-200 bg-white hover:border-teal-200'
                  }`}
                  data-testid={`encare-patient-${ep.encare_user_id}`}
                >
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${ep.already_synced ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-500'}`}>
                        <User className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-slate-900">{ep.name}</h3>
                          <Badge variant="outline" className="text-xs font-mono">{ep.encare_user_id}</Badge>
                          {ep.already_synced && (
                            <Badge className="bg-green-100 text-green-700 border-green-200 text-xs">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Synced
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-500">
                          {ep.phone}{ep.city ? ` - ${ep.city}` : ''}
                        </p>
                        {ep.diseases_hint?.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {ep.diseases_hint.map((m, i) => (
                              <Badge key={i} variant="outline" className="text-xs bg-white">{m}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 items-center">
                      {ep.already_synced ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-teal-200 text-teal-700"
                            onClick={() => handleSync(ep.encare_user_id, "medications")}
                            disabled={syncing[`${ep.encare_user_id}-medications`]}
                            data-testid={`sync-meds-${ep.encare_user_id}`}
                          >
                            {syncing[`${ep.encare_user_id}-medications`] ? (
                              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Pill className="h-3 w-3 mr-1" />
                            )}
                            Re-sync Meds
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-teal-200 text-teal-700"
                            onClick={() => handleSync(ep.encare_user_id, "vitals")}
                            disabled={syncing[`${ep.encare_user_id}-vitals`]}
                            data-testid={`sync-vitals-${ep.encare_user_id}`}
                          >
                            {syncing[`${ep.encare_user_id}-vitals`] ? (
                              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                            ) : (
                              <Activity className="h-3 w-3 mr-1" />
                            )}
                            Sync Vitals
                          </Button>
                          <Link to={`/patients/${ep.crm_patient_id}`}>
                            <Button size="sm" variant="ghost" className="text-teal-600" data-testid={`view-patient-${ep.encare_user_id}`}>
                              View <ArrowRight className="h-3 w-3 ml-1" />
                            </Button>
                          </Link>
                        </>
                      ) : (
                        <Button
                          size="sm"
                          className="gradient-teal text-white"
                          onClick={() => handleSyncAll(ep.encare_user_id)}
                          disabled={syncing[`${ep.encare_user_id}-all`]}
                          data-testid={`import-patient-${ep.encare_user_id}`}
                        >
                          {syncing[`${ep.encare_user_id}-all`] ? (
                            <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                          ) : (
                            <Download className="h-3 w-3 mr-1" />
                          )}
                          Import to CRM
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sync Activity Log */}
      <Card data-testid="sync-logs-card">
        <CardHeader>
          <CardTitle className="text-lg font-['Manrope'] flex items-center gap-2">
            <Clock className="h-5 w-5 text-teal-500" />
            Sync Activity Log
          </CardTitle>
        </CardHeader>
        <CardContent>
          {syncLogs.length === 0 ? (
            <p className="text-center text-slate-500 py-6">No sync activity yet</p>
          ) : (
            <div className="space-y-2">
              {syncLogs.slice(0, 20).map((log, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 text-sm" data-testid={`sync-log-${i}`}>
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                  <div className="flex-1">
                    <span className="font-medium text-slate-700">{log.patient_name}</span>
                    <span className="text-slate-400 mx-2">-</span>
                    <span className="text-slate-600">{log.details}</span>
                  </div>
                  <Badge variant="outline" className="text-xs capitalize">{log.sync_type}</Badge>
                  <span className="text-xs text-slate-400 whitespace-nowrap">
                    {new Date(log.synced_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
