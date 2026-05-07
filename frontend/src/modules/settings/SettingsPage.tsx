import { useState } from 'react'
import { Save, User, Bell, Shield, Building2 } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'

const tabs = [
  { id: 'company', label: 'Company', icon: Building2 },
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
]

function Field({ label, defaultValue, type = 'text', disabled = false }: { label: string; defaultValue?: string; type?: string; disabled?: boolean }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1.5">{label}</label>
      <input type={type} defaultValue={defaultValue} disabled={disabled}
        className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-800 outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100 disabled:opacity-50 disabled:cursor-not-allowed" />
    </div>
  )
}

function Toggle({ label, sub, defaultChecked = false }: { label: string; sub?: string; defaultChecked?: boolean }) {
  const [on, setOn] = useState(defaultChecked)
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-50 last:border-0">
      <div>
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
      <button onClick={()=>setOn(!on)} className={`relative h-5 w-9 rounded-full transition-colors ${on?'bg-brand-600':'bg-slate-200'}`}>
        <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${on?'translate-x-4':'translate-x-0.5'}`} />
      </button>
    </div>
  )
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('company')

  return (
    <div className="space-y-5">
      <PageHeader title="Settings" subtitle="Manage your account, company, and system preferences" />

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar tabs */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  activeTab === tab.id ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3 space-y-4">
          {activeTab === 'company' && (
            <Card>
              <CardHeader><CardTitle className="text-base">Company Information</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Company Name" defaultValue="Arjun Distribution Pvt Ltd" />
                  <Field label="GSTIN" defaultValue="27AABCA1234A1Z5" />
                  <Field label="PAN" defaultValue="AABCA1234A" />
                  <Field label="Industry" defaultValue="Distribution" />
                  <Field label="City" defaultValue="Mumbai" />
                  <Field label="State" defaultValue="Maharashtra" />
                </div>
                <Field label="Registered Address" defaultValue="Plot 14, MIDC Industrial Area, Andheri East, Mumbai - 400093" />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Invoice Tolerance (%)" defaultValue="2" type="number" />
                  <Field label="Payment Terms (days)" defaultValue="30" type="number" />
                </div>
                <div className="pt-2">
                  <Button className="gap-2"><Save size={14}/> Save Changes</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'profile' && (
            <Card>
              <CardHeader><CardTitle className="text-base">My Profile</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-full bg-brand-100 flex items-center justify-center text-brand-700 text-xl font-bold">AD</div>
                  <Button variant="outline" size="sm">Change Photo</Button>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label="Full Name" defaultValue="Amit Desai" />
                  <Field label="Email" defaultValue="amit.desai@arjundist.com" />
                  <Field label="Phone" defaultValue="+91 98765 43210" />
                  <Field label="Role" defaultValue="Admin" disabled />
                </div>
                <div className="pt-2"><Button className="gap-2"><Save size={14}/> Save Profile</Button></div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <CardHeader><CardTitle className="text-base">Notification Preferences</CardTitle></CardHeader>
              <CardContent>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Critical Alerts</p>
                  <Toggle label="Invoice overdue alerts" sub="Get notified when invoices pass their due date" defaultChecked />
                  <Toggle label="Three-way match failures" sub="Alert when vendor invoice doesn't match PO or GRN" defaultChecked />
                  <Toggle label="Vendor acknowledgement expiry" sub="48-hour vendor acknowledgement timer warnings" defaultChecked />
                </div>
                <div className="mt-4">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Operational Alerts</p>
                  <Toggle label="New order approvals required" defaultChecked />
                  <Toggle label="GRN created notifications" />
                  <Toggle label="Payment reconciliation suggestions" defaultChecked />
                  <Toggle label="Daily summary digest" sub="Receive a daily email summary at 9 AM" defaultChecked />
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <CardHeader><CardTitle className="text-base">Security Settings</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Change Password</p>
                  <div className="space-y-3 max-w-sm">
                    <Field label="Current Password" type="password" />
                    <Field label="New Password" type="password" />
                    <Field label="Confirm New Password" type="password" />
                  </div>
                  <div className="mt-3"><Button size="sm">Update Password</Button></div>
                </div>
                <div className="pt-2 border-t border-slate-100">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Two-Factor Authentication</p>
                  <Toggle label="Enable 2FA" sub="Adds an extra layer of security to your account" />
                </div>
                <div className="pt-2 border-t border-slate-100">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Active Sessions</p>
                  {[
                    { device: 'Chrome on MacOS', location: 'Mumbai, IN', time: 'Active now', current: true },
                    { device: 'Mobile App — Android', location: 'Mumbai, IN', time: '2 hours ago', current: false },
                  ].map(s => (
                    <div key={s.device} className="flex items-center justify-between py-2.5 border-b border-slate-50 last:border-0">
                      <div>
                        <p className="text-sm font-medium text-slate-700">{s.device}</p>
                        <p className="text-xs text-slate-400">{s.location} · {s.time}</p>
                      </div>
                      {s.current ? <span className="text-xs font-semibold text-green-600">Current</span>
                        : <button className="text-xs text-red-500 hover:underline">Revoke</button>}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
