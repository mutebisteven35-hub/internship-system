import {
  Bell,
  BookOpen,
  Building2,
  Check,
  ClipboardList,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  LogOut,
  NotebookPen,
  Plus,
  Settings,
  ShieldCheck,
  Star,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "./api";
import { useAuth } from "./AuthContext";

const APP_SHORT_NAME = "ILES";
const APP_FULL_NAME = "INTERNSHIP LOGGING AND EVALUATION SYSTEM";
const APP_DISPLAY_NAME = `${APP_FULL_NAME} (${APP_SHORT_NAME})`;
const today = () => new Date().toISOString().slice(0, 10);

function useLoad(loader, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      setData(await loader());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, deps);

  return { data, setData, error, loading, refresh };
}

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <FullScreenStatus text="Loading your workspace..." />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function FullScreenStatus({ text }) {
  return <main className="center-screen">{text}</main>;
}

function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const nav = [
    { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/app/internship", label: "Internship", icon: Building2 },
    { to: "/app/logbook", label: "Logbook", icon: NotebookPen },
    { to: "/app/evaluations", label: "Evaluations", icon: Star },
    { to: "/app/courses", label: "Courses", icon: BookOpen },
    { to: "/app/assignments", label: "Assignments", icon: ClipboardList },
    { to: "/app/notifications", label: "Notifications", icon: Bell },
    { to: "/app/password", label: "Change Password", icon: KeyRound },
    ...(user?.role === "admin" ? [{ to: "/app/admin", label: "Admin", icon: Settings }] : []),
  ];

  async function onLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <GraduationCap aria-hidden="true" />
          <div>
            <strong className="brand-full-name">{APP_DISPLAY_NAME}</strong>
            <span>Learning workspace</span>
          </div>
        </div>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                <Icon aria-hidden="true" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <div className="identity">
            <UserRound aria-hidden="true" />
            <span>{user?.display_name}</span>
            <small>{user?.role}</small>
          </div>
          <button className="icon-text" onClick={onLogout} title="Log out">
            <LogOut aria-hidden="true" />
            <span>Log out</span>
          </button>
        </header>
        <main className="content">
          <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="internship" element={<Internship />} />
            <Route path="logbook" element={<Logbook />} />
            <Route path="evaluations" element={<Evaluations />} />
            <Route path="courses" element={<Courses />} />
            <Route path="courses/:id" element={<CourseDetail />} />
            <Route path="assignments" element={<Assignments />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="password" element={<ChangePassword />} />
            <Route path="admin" element={user?.role === "admin" ? <Admin /> : <Navigate to="/app/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function Login() {
  const { user, login } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState("student");
  const [password, setPassword] = useState("Passw0rd!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const successMessage = location.state?.message;

  if (user) return <Navigate to="/app/dashboard" replace />;

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div className="brand login-brand">
          <GraduationCap aria-hidden="true" />
          <div>
            <strong className="brand-full-name">{APP_DISPLAY_NAME}</strong>
            <span>Account access</span>
          </div>
        </div>
        <form onSubmit={submit}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoFocus />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <Link className="text-link" to="/forgot-password">
            Forgot password?
          </Link>
          {successMessage && <p className="success">{successMessage}</p>}
          {error && <p className="error">{error}</p>}
          <button className="primary" disabled={busy}>
            <ShieldCheck aria-hidden="true" />
            <span>{busy ? "Signing in..." : "Sign in"}</span>
          </button>
        </form>
        <div className="demo-logins">
          <button onClick={() => setUsername("admin")}>admin</button>
          <button onClick={() => setUsername("instructor")}>instructor</button>
          <button onClick={() => setUsername("student")}>student</button>
        </div>
      </section>
    </main>
  );
}

function ForgotPassword() {
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function requestReset(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const data = await api.requestPasswordReset({ identifier });
      setIdentifier(data.identifier || identifier);
      setResetCode(data.reset_code || "");
      setMessage(data.detail);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function confirmReset(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api.confirmPasswordReset({
        identifier,
        reset_code: resetCode,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      navigate("/login", { replace: true, state: { message: data.detail } });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div className="brand login-brand">
          <KeyRound aria-hidden="true" />
          <div>
            <strong>Password reset</strong>
            <span>{APP_DISPLAY_NAME} account access</span>
          </div>
        </div>
        <form onSubmit={requestReset}>
          <label>
            Username or email
            <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoFocus required />
          </label>
          <button className="primary" disabled={busy}>
            <KeyRound aria-hidden="true" />
            <span>{busy ? "Requesting..." : "Request reset code"}</span>
          </button>
        </form>
        {resetCode && (
          <form className="reset-confirm-form" onSubmit={confirmReset}>
            <div className="reset-code">
              <span>Reset code</span>
              <code>{resetCode}</code>
            </div>
            <label>
              New password
              <input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required />
            </label>
            <label>
              Confirm new password
              <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required />
            </label>
            <button className="primary" disabled={busy}>
              <Check aria-hidden="true" />
              <span>{busy ? "Resetting..." : "Reset password"}</span>
            </button>
          </form>
        )}
        {message && <p className="success">{message}</p>}
        {error && <p className="error">{error}</p>}
        <Link className="text-link auth-back-link" to="/login">
          Back to login
        </Link>
      </section>
    </main>
  );
}

function ChangePassword() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api.changePassword(form);
      await logout();
      navigate("/login", { replace: true, state: { message: data.detail } });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Change password" subtitle={`Update your ${APP_DISPLAY_NAME} account password.`}>
      <section className="panel narrow-panel">
        <form className="compact-form no-top-border" onSubmit={submit}>
          <label>
            Current password
            <input
              type="password"
              value={form.current_password}
              onChange={(event) => setForm({ ...form, current_password: event.target.value })}
              required
            />
          </label>
          <label>
            New password
            <input
              type="password"
              value={form.new_password}
              onChange={(event) => setForm({ ...form, new_password: event.target.value })}
              required
            />
          </label>
          <label>
            Confirm new password
            <input
              type="password"
              value={form.confirm_password}
              onChange={(event) => setForm({ ...form, confirm_password: event.target.value })}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={busy}>
            <KeyRound aria-hidden="true" />
            <span>{busy ? "Changing..." : "Change password"}</span>
          </button>
        </form>
      </section>
    </Page>
  );
}

function LandingPage() {
  const { user, loading } = useAuth();
  const proceedTo = user ? "/app/dashboard" : "/login";

  return (
    <main className="landing-screen" aria-label={APP_SHORT_NAME}>
      <h1 className="landing-title">{APP_FULL_NAME}</h1>
      <Link className="welcome-action" to={loading ? "#" : proceedTo} aria-disabled={loading}>
        Proceed
      </Link>
    </main>
  );
}

function Dashboard() {
  const { data, error, loading } = useLoad(api.dashboard);
  const stats = data ? Object.entries(data).filter(([key]) => key !== "role") : [];
  return (
    <Page title="Dashboard" subtitle="Current academic activity and workflow status.">
      <Status error={error} loading={loading} />
      <div className="metric-grid">
        {stats.map(([key, value]) => (
          <article className="metric" key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
    </Page>
  );
}

function Internship() {
  const { data: placements = [], error, loading } = useLoad(api.placements);

  return (
    <Page title="Internship" subtitle="Student placements, host organizations, workplace supervisors, and objectives.">
      <Status error={error} loading={loading} />
      <div className="card-grid">
        {placements?.map((placement) => (
          <article className="card course-card" key={placement.id}>
            <div className="card-head">
              <span className="code">{placement.position_title}</span>
              <span className={`pill ${placement.status}`}>{placement.status}</span>
            </div>
            <h2>{placement.host_organization_detail?.name}</h2>
            <p>{placement.learning_objectives || "No learning objectives recorded yet."}</p>
            <dl>
              <div>
                <dt>Student</dt>
                <dd>{placement.student_detail?.display_name}</dd>
              </div>
              <div>
                <dt>Instructor</dt>
                <dd>{placement.instructor_detail?.display_name}</dd>
              </div>
              <div>
                <dt>Host supervisor</dt>
                <dd>{placement.workplace_supervisor_name || "Not set"}</dd>
              </div>
              <div>
                <dt>Period</dt>
                <dd>{placement.start_date} to {placement.end_date}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
      <ListEmpty items={placements || []} label="No internship placements yet." />
    </Page>
  );
}

function Logbook() {
  const { user } = useAuth();
  const placements = useLoad(api.placements);
  const entries = useLoad(api.logbookEntries);
  const attendance = useLoad(api.attendanceRecords);
  const firstPlacementId = placements.data?.[0]?.id || "";
  const [entryForm, setEntryForm] = useState({
    placement: "",
    entry_date: today(),
    hours_worked: 8,
    activities: "",
    skills_learned: "",
    challenges: "",
    next_plan: "",
  });
  const [attendanceForm, setAttendanceForm] = useState({
    placement: "",
    date: today(),
    status: "present",
    check_in: "08:00",
    check_out: "17:00",
    notes: "",
  });
  const [feedbackByEntry, setFeedbackByEntry] = useState({});
  const [actionError, setActionError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [entryMessage, setEntryMessage] = useState("");
  const [entryError, setEntryError] = useState("");
  const [attendanceMessage, setAttendanceMessage] = useState("");
  const [attendanceError, setAttendanceError] = useState("");
  const [submitMessageByEntry, setSubmitMessageByEntry] = useState({});
  const [savingAction, setSavingAction] = useState("");

  useEffect(() => {
    if (!firstPlacementId) return;
    setEntryForm((form) => (form.placement ? form : { ...form, placement: firstPlacementId }));
    setAttendanceForm((form) => (form.placement ? form : { ...form, placement: firstPlacementId }));
  }, [firstPlacementId]);

  async function createEntry(event) {
    event.preventDefault();
    setActionError("");
    setActionMessage("");
    setEntryError("");
    setEntryMessage("");
    setSavingAction("entry");
    try {
      await api.createLogbookEntry(entryForm);
      setEntryForm({ ...entryForm, activities: "", skills_learned: "", challenges: "", next_plan: "" });
      await entries.refresh();
      setActionMessage("Logbook entry saved. You can submit it when it is ready for review.");
      setEntryMessage("Logbook entry saved. It now appears in the Logbook entries list below.");
    } catch (err) {
      setActionError(err.message);
      setEntryError(err.message);
    } finally {
      setSavingAction("");
    }
  }

  async function createAttendance(event) {
    event.preventDefault();
    setActionError("");
    setActionMessage("");
    setAttendanceError("");
    setAttendanceMessage("");
    setSavingAction("attendance");
    try {
      await api.createAttendanceRecord(attendanceForm);
      setAttendanceForm({ ...attendanceForm, notes: "" });
      await attendance.refresh();
      setActionMessage("Attendance record saved.");
      setAttendanceMessage("Attendance record saved. It now appears in the Attendance records list below.");
    } catch (err) {
      setActionError(err.message);
      setAttendanceError(err.message);
    } finally {
      setSavingAction("");
    }
  }

  async function submitEntry(entry) {
    setActionError("");
    setActionMessage("");
    setSubmitMessageByEntry({ ...submitMessageByEntry, [entry.id]: "" });
    setSavingAction(`submit-${entry.id}`);
    try {
      await api.submitLogbookEntry(entry.id);
      await entries.refresh();
      setActionMessage("Logbook entry submitted to the instructor.");
      setSubmitMessageByEntry({ ...submitMessageByEntry, [entry.id]: "Submitted to the instructor." });
    } catch (err) {
      setActionError(err.message);
    } finally {
      setSavingAction("");
    }
  }

  async function reviewEntry(entry) {
    setActionError("");
    setActionMessage("");
    setSavingAction(`review-${entry.id}`);
    try {
      await api.reviewLogbookEntry(entry.id, { instructor_feedback: feedbackByEntry[entry.id] || "" });
      setFeedbackByEntry({ ...feedbackByEntry, [entry.id]: "" });
      await entries.refresh();
      setActionMessage("Logbook entry reviewed.");
    } catch (err) {
      setActionError(err.message);
    } finally {
      setSavingAction("");
    }
  }

  return (
    <Page title="Logbook" subtitle="Daily internship activities, attendance, skills learned, challenges, and instructor review.">
      <Status error={placements.error || entries.error || attendance.error} loading={placements.loading || entries.loading} />
      {actionMessage && <p className="success">{actionMessage}</p>}
      {actionError && <p className="error">{actionError}</p>}
      <section className="detail-layout">
        {user?.role === "student" && (
          <article className="panel">
            <h2>New logbook entry</h2>
            {entryMessage && <p className="success">{entryMessage}</p>}
            {entryError && <p className="error">{entryError}</p>}
            <form className="compact-form no-top-border" onSubmit={createEntry}>
              <select value={entryForm.placement} onChange={(e) => setEntryForm({ ...entryForm, placement: e.target.value })} required>
                <option value="">Placement</option>
                {(placements.data || []).map((item) => <option key={item.id} value={item.id}>{item.host_organization_detail?.name}</option>)}
              </select>
              <input type="date" value={entryForm.entry_date} onChange={(e) => setEntryForm({ ...entryForm, entry_date: e.target.value })} required />
              <input type="number" min="0" step="0.5" value={entryForm.hours_worked} onChange={(e) => setEntryForm({ ...entryForm, hours_worked: e.target.value })} required />
              <textarea placeholder="Activities done" value={entryForm.activities} onChange={(e) => setEntryForm({ ...entryForm, activities: e.target.value })} required />
              <textarea placeholder="Skills learned" value={entryForm.skills_learned} onChange={(e) => setEntryForm({ ...entryForm, skills_learned: e.target.value })} />
              <textarea placeholder="Challenges" value={entryForm.challenges} onChange={(e) => setEntryForm({ ...entryForm, challenges: e.target.value })} />
              <textarea placeholder="Plan for next day or week" value={entryForm.next_plan} onChange={(e) => setEntryForm({ ...entryForm, next_plan: e.target.value })} />
              <button disabled={savingAction === "entry"}>
                <Plus aria-hidden="true" />
                <span>{savingAction === "entry" ? "Saving..." : "Save entry"}</span>
              </button>
            </form>
          </article>
        )}
        {user?.role === "student" && (
          <article className="panel">
            <h2>Attendance</h2>
            {attendanceMessage && <p className="success">{attendanceMessage}</p>}
            {attendanceError && <p className="error">{attendanceError}</p>}
            <form className="compact-form no-top-border" onSubmit={createAttendance}>
              <select value={attendanceForm.placement} onChange={(e) => setAttendanceForm({ ...attendanceForm, placement: e.target.value })} required>
                <option value="">Placement</option>
                {(placements.data || []).map((item) => <option key={item.id} value={item.id}>{item.host_organization_detail?.name}</option>)}
              </select>
              <input type="date" value={attendanceForm.date} onChange={(e) => setAttendanceForm({ ...attendanceForm, date: e.target.value })} required />
              <select value={attendanceForm.status} onChange={(e) => setAttendanceForm({ ...attendanceForm, status: e.target.value })}>
                <option value="present">Present</option>
                <option value="late">Late</option>
                <option value="remote">Remote</option>
                <option value="absent">Absent</option>
              </select>
              <input type="time" value={attendanceForm.check_in} onChange={(e) => setAttendanceForm({ ...attendanceForm, check_in: e.target.value })} />
              <input type="time" value={attendanceForm.check_out} onChange={(e) => setAttendanceForm({ ...attendanceForm, check_out: e.target.value })} />
              <textarea placeholder="Notes" value={attendanceForm.notes} onChange={(e) => setAttendanceForm({ ...attendanceForm, notes: e.target.value })} />
              <button disabled={savingAction === "attendance"}>
                <Check aria-hidden="true" />
                <span>{savingAction === "attendance" ? "Saving..." : "Record attendance"}</span>
              </button>
            </form>
          </article>
        )}
        <article className="panel span-two">
          <h2>Logbook entries</h2>
          <ListEmpty items={entries.data || []} label="No logbook entries yet." />
          {(entries.data || []).map((entry) => (
            <div className="list-row action-row" key={entry.id}>
              <div>
                <strong>{entry.entry_date} - {entry.placement_detail?.host_organization_detail?.name}</strong>
                <span>{entry.student_detail?.display_name} - {entry.status} - {entry.hours_worked} hours</span>
                <p>{entry.activities}</p>
                {entry.instructor_feedback && <p className="success">Feedback: {entry.instructor_feedback}</p>}
                {submitMessageByEntry[entry.id] && <p className="success">{submitMessageByEntry[entry.id]}</p>}
              </div>
              <div className="grade-form">
                {user?.role === "student" && entry.status === "draft" && (
                  <button disabled={savingAction === `submit-${entry.id}`} onClick={() => submitEntry(entry)}>
                    {savingAction === `submit-${entry.id}` ? "Submitting..." : "Submit"}
                  </button>
                )}
                {user?.role !== "student" && entry.status === "submitted" && (
                  <>
                    <input placeholder="Feedback" value={feedbackByEntry[entry.id] || ""} onChange={(e) => setFeedbackByEntry({ ...feedbackByEntry, [entry.id]: e.target.value })} />
                    <button disabled={savingAction === `review-${entry.id}`} onClick={() => reviewEntry(entry)}>
                      {savingAction === `review-${entry.id}` ? "Reviewing..." : "Review"}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </article>
        <article className="panel span-two">
          <h2>Attendance records</h2>
          <ListEmpty items={attendance.data || []} label="No attendance records yet." />
          {(attendance.data || []).map((record) => (
            <div className="list-row" key={record.id}>
              <strong>{record.date} - {record.placement_detail?.host_organization_detail?.name}</strong>
              <span>{record.student_detail?.display_name} - {record.status}</span>
              <p>
                {record.check_in || "--"} to {record.check_out || "--"}
                {record.notes ? ` - ${record.notes}` : ""}
              </p>
            </div>
          ))}
        </article>
      </section>
    </Page>
  );
}

function Evaluations() {
  const { user } = useAuth();
  const placements = useLoad(api.placements);
  const evaluations = useLoad(api.internshipEvaluations);
  const [form, setForm] = useState({
    placement: "",
    evaluator_role: "instructor",
    technical_score: 20,
    professionalism_score: 20,
    communication_score: 20,
    attendance_score: 20,
    comments: "",
    recommendation: "",
  });

  useEffect(() => {
    const placement = placements.data?.[0]?.id;
    if (placement && !form.placement) setForm((current) => ({ ...current, placement }));
  }, [placements.data]);

  async function createEvaluation(event) {
    event.preventDefault();
    await api.createInternshipEvaluation(form);
    setForm({ ...form, comments: "", recommendation: "" });
    evaluations.refresh();
  }

  return (
    <Page title="Evaluations" subtitle="Internship assessment scores, comments, and recommendations.">
      <Status error={placements.error || evaluations.error} loading={placements.loading || evaluations.loading} />
      {user?.role !== "student" && (
        <section className="panel narrow-panel">
          <h2>New evaluation</h2>
          <form className="compact-form no-top-border" onSubmit={createEvaluation}>
            <select value={form.placement} onChange={(e) => setForm({ ...form, placement: e.target.value })} required>
              <option value="">Placement</option>
              {(placements.data || []).map((item) => (
                <option key={item.id} value={item.id}>{item.student_detail?.display_name} - {item.host_organization_detail?.name}</option>
              ))}
            </select>
            <select value={form.evaluator_role} onChange={(e) => setForm({ ...form, evaluator_role: e.target.value })}>
              <option value="instructor">Instructor</option>
              <option value="host_supervisor">Host Supervisor</option>
            </select>
            <input type="number" min="0" max="25" value={form.technical_score} onChange={(e) => setForm({ ...form, technical_score: e.target.value })} />
            <input type="number" min="0" max="25" value={form.professionalism_score} onChange={(e) => setForm({ ...form, professionalism_score: e.target.value })} />
            <input type="number" min="0" max="25" value={form.communication_score} onChange={(e) => setForm({ ...form, communication_score: e.target.value })} />
            <input type="number" min="0" max="25" value={form.attendance_score} onChange={(e) => setForm({ ...form, attendance_score: e.target.value })} />
            <textarea placeholder="Comments" value={form.comments} onChange={(e) => setForm({ ...form, comments: e.target.value })} />
            <textarea placeholder="Recommendation" value={form.recommendation} onChange={(e) => setForm({ ...form, recommendation: e.target.value })} />
            <button><Star aria-hidden="true" /><span>Save evaluation</span></button>
          </form>
        </section>
      )}
      <div className="wide-list">
        {(evaluations.data || []).map((evaluation) => (
          <article className="panel" key={evaluation.id}>
            <div className="card-head">
              <span className="code">{evaluation.placement_detail?.student_detail?.display_name}</span>
              <span className="pill">{evaluation.total_score}/100</span>
            </div>
            <h2>{evaluation.placement_detail?.host_organization_detail?.name}</h2>
            <p>{evaluation.comments || "No comments recorded."}</p>
            <dl>
              <div><dt>Technical</dt><dd>{evaluation.technical_score}/25</dd></div>
              <div><dt>Professionalism</dt><dd>{evaluation.professionalism_score}/25</dd></div>
              <div><dt>Communication</dt><dd>{evaluation.communication_score}/25</dd></div>
              <div><dt>Attendance</dt><dd>{evaluation.attendance_score}/25</dd></div>
            </dl>
            {evaluation.recommendation && <p className="success">Recommendation: {evaluation.recommendation}</p>}
          </article>
        ))}
      </div>
    </Page>
  );
}

function Courses() {
  const { user } = useAuth();
  const { data: courses = [], error, loading, refresh } = useLoad(api.courses);

  async function register(course) {
    await api.registerCourse(course.id);
    refresh();
  }

  return (
    <Page title="Courses" subtitle="Browse active courses, registrations, and teaching assignments.">
      <Status error={error} loading={loading} />
      <div className="card-grid">
        {courses?.map((course) => (
          <article className="card course-card" key={course.id}>
            <div className="card-head">
              <span className="code">{course.code}</span>
              <span className={`pill ${course.enrollment_status || course.status}`}>{course.enrollment_status || course.status}</span>
            </div>
            <h2>{course.title}</h2>
            <p>{course.description}</p>
            <dl>
              <div>
                <dt>Instructor</dt>
                <dd>{course.instructor_detail?.display_name}</dd>
              </div>
              <div>
                <dt>Approved</dt>
                <dd>{course.enrollment_count}/{course.capacity}</dd>
              </div>
            </dl>
            <div className="row-actions">
              <Link className="secondary button-link" to={`/app/courses/${course.id}`}>
                Open
              </Link>
              {user?.role === "student" && !course.enrollment_status && (
                <button onClick={() => register(course)}>
                  <Plus aria-hidden="true" />
                  <span>Register</span>
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </Page>
  );
}

function CourseDetail() {
  const { user } = useAuth();
  const { id } = useParams();
  const { data: course, error, loading, refresh } = useLoad(() => api.course(id), [id]);
  const materials = useLoad(api.materials, [id]);
  const assignments = useLoad(api.assignments, [id]);
  const enrollments = useLoad(api.enrollments, [id]);
  const [material, setMaterial] = useState({ title: "", material_type: "note", body: "", url: "" });
  const [assignment, setAssignment] = useState({ title: "", instructions: "", due_at: "", max_score: 100 });
  const canManage = user?.role === "admin" || course?.instructor_detail?.id === user?.id;

  async function addMaterial(event) {
    event.preventDefault();
    await api.createMaterial({ ...material, course: Number(id) });
    setMaterial({ title: "", material_type: "note", body: "", url: "" });
    materials.refresh();
  }

  async function addAssignment(event) {
    event.preventDefault();
    await api.createAssignment({ ...assignment, course: Number(id), max_score: Number(assignment.max_score) });
    setAssignment({ title: "", instructions: "", due_at: "", max_score: 100 });
    assignments.refresh();
  }

  async function decide(enrollment, action) {
    if (action === "approve") await api.approveEnrollment(enrollment.id);
    if (action === "reject") await api.rejectEnrollment(enrollment.id);
    enrollments.refresh();
    refresh();
  }

  const courseMaterials = (materials.data || []).filter((item) => item.course === Number(id));
  const courseAssignments = (assignments.data || []).filter((item) => item.course === Number(id));
  const courseEnrollments = (enrollments.data || []).filter((item) => item.course === Number(id));

  return (
    <Page title={course?.title || "Course"} subtitle={course ? `${course.code} - ${course.term_detail?.name}` : ""}>
      <Status error={error || materials.error || assignments.error || enrollments.error} loading={loading} />
      {course && (
        <section className="detail-layout">
          <article className="panel">
            <h2>Overview</h2>
            <p>{course.description}</p>
            <dl className="stacked">
              <div>
                <dt>Program</dt>
                <dd>{course.program_detail?.name}</dd>
              </div>
              <div>
                <dt>Instructor</dt>
                <dd>{course.instructor_detail?.display_name}</dd>
              </div>
              <div>
                <dt>Capacity</dt>
                <dd>{course.enrollment_count}/{course.capacity}</dd>
              </div>
            </dl>
          </article>
          <article className="panel">
            <h2>Learning Materials</h2>
            <ListEmpty items={courseMaterials} label="No materials yet." />
            {courseMaterials.map((item) => (
              <div className="list-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.material_type}</span>
                  <p>{item.body || item.url}</p>
                </div>
              </div>
            ))}
            {canManage && (
              <form className="compact-form" onSubmit={addMaterial}>
                <input placeholder="Material title" value={material.title} onChange={(e) => setMaterial({ ...material, title: e.target.value })} required />
                <select value={material.material_type} onChange={(e) => setMaterial({ ...material, material_type: e.target.value })}>
                  <option value="note">Note</option>
                  <option value="link">Link</option>
                  <option value="video">Video</option>
                  <option value="file">File</option>
                </select>
                <input placeholder="URL" value={material.url} onChange={(e) => setMaterial({ ...material, url: e.target.value })} />
                <textarea placeholder="Body" value={material.body} onChange={(e) => setMaterial({ ...material, body: e.target.value })} />
                <button>
                  <Plus aria-hidden="true" />
                  <span>Add material</span>
                </button>
              </form>
            )}
          </article>
          <article className="panel">
            <h2>Assignments</h2>
            <ListEmpty items={courseAssignments} label="No assignments yet." />
            {courseAssignments.map((item) => (
              <div className="list-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <span>Due {new Date(item.due_at).toLocaleString()}</span>
                  <p>{item.instructions}</p>
                </div>
              </div>
            ))}
            {canManage && (
              <form className="compact-form" onSubmit={addAssignment}>
                <input placeholder="Assignment title" value={assignment.title} onChange={(e) => setAssignment({ ...assignment, title: e.target.value })} required />
                <textarea placeholder="Instructions" value={assignment.instructions} onChange={(e) => setAssignment({ ...assignment, instructions: e.target.value })} required />
                <input type="datetime-local" value={assignment.due_at} onChange={(e) => setAssignment({ ...assignment, due_at: e.target.value })} required />
                <input type="number" min="1" value={assignment.max_score} onChange={(e) => setAssignment({ ...assignment, max_score: e.target.value })} />
                <button>
                  <Plus aria-hidden="true" />
                  <span>Add assignment</span>
                </button>
              </form>
            )}
          </article>
          {canManage && (
            <article className="panel">
              <h2>Registrations</h2>
              <ListEmpty items={courseEnrollments} label="No registrations yet." />
              {courseEnrollments.map((item) => (
                <div className="list-row action-row" key={item.id}>
                  <div>
                    <strong>{item.student_detail?.display_name}</strong>
                    <span>{item.status}</span>
                  </div>
                  {item.status === "pending" && (
                    <div className="row-actions">
                      <button onClick={() => decide(item, "approve")}>
                        <Check aria-hidden="true" />
                        <span>Approve</span>
                      </button>
                      <button className="secondary" onClick={() => decide(item, "reject")}>
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </article>
          )}
        </section>
      )}
    </Page>
  );
}

function Assignments() {
  const { user } = useAuth();
  const assignments = useLoad(api.assignments);
  const submissions = useLoad(api.submissions);
  const [textByAssignment, setTextByAssignment] = useState({});
  const [gradeBySubmission, setGradeBySubmission] = useState({});

  async function submitWork(assignment) {
    await api.createSubmission({ assignment: assignment.id, text: textByAssignment[assignment.id] || "" });
    setTextByAssignment({ ...textByAssignment, [assignment.id]: "" });
    submissions.refresh();
    assignments.refresh();
  }

  async function grade(submission) {
    const payload = gradeBySubmission[submission.id] || {};
    await api.gradeSubmission(submission.id, { score: payload.score || 0, feedback: payload.feedback || "" });
    submissions.refresh();
  }

  const studentSubmissionByAssignment = useMemo(() => {
    return Object.fromEntries((submissions.data || []).map((submission) => [submission.assignment, submission]));
  }, [submissions.data]);

  return (
    <Page title="Assignments" subtitle="Submit coursework, review submissions, and post grades.">
      <Status error={assignments.error || submissions.error} loading={assignments.loading || submissions.loading} />
      <div className="wide-list">
        {(assignments.data || []).map((assignment) => (
          <article className="panel" key={assignment.id}>
            <div className="card-head">
              <span className="code">{assignment.course_detail?.code}</span>
              <span className="pill">Due {new Date(assignment.due_at).toLocaleDateString()}</span>
            </div>
            <h2>{assignment.title}</h2>
            <p>{assignment.instructions}</p>
            {user?.role === "student" && (
              <div className="submission-box">
                {studentSubmissionByAssignment[assignment.id] ? (
                  <p className="success">Submitted: {studentSubmissionByAssignment[assignment.id].status}</p>
                ) : (
                  <>
                    <textarea
                      placeholder="Write your submission text"
                      value={textByAssignment[assignment.id] || ""}
                      onChange={(e) => setTextByAssignment({ ...textByAssignment, [assignment.id]: e.target.value })}
                    />
                    <button onClick={() => submitWork(assignment)}>
                      <Check aria-hidden="true" />
                      <span>Submit</span>
                    </button>
                  </>
                )}
              </div>
            )}
          </article>
        ))}
      </div>
      {user?.role !== "student" && (
        <section className="panel">
          <h2>Submissions</h2>
          <ListEmpty items={submissions.data || []} label="No submissions yet." />
          {(submissions.data || []).map((submission) => (
            <div className="list-row action-row" key={submission.id}>
              <div>
                <strong>{submission.student_detail?.display_name}</strong>
                <span>{submission.assignment_detail?.title} - {submission.status}</span>
                <p>{submission.text}</p>
              </div>
              <div className="grade-form">
                <input
                  type="number"
                  placeholder="Score"
                  value={gradeBySubmission[submission.id]?.score || ""}
                  onChange={(e) =>
                    setGradeBySubmission({
                      ...gradeBySubmission,
                      [submission.id]: { ...gradeBySubmission[submission.id], score: e.target.value },
                    })
                  }
                />
                <input
                  placeholder="Feedback"
                  value={gradeBySubmission[submission.id]?.feedback || ""}
                  onChange={(e) =>
                    setGradeBySubmission({
                      ...gradeBySubmission,
                      [submission.id]: { ...gradeBySubmission[submission.id], feedback: e.target.value },
                    })
                  }
                />
                <button onClick={() => grade(submission)}>Grade</button>
              </div>
            </div>
          ))}
        </section>
      )}
    </Page>
  );
}

function Notifications() {
  const { data = [], error, loading, refresh } = useLoad(api.notifications);

  async function markRead(notification) {
    await api.markNotificationRead(notification.id);
    refresh();
  }

  return (
    <Page title="Notifications" subtitle="Registration, assignment, and grade updates.">
      <Status error={error} loading={loading} />
      <div className="wide-list">
        {data?.map((notification) => (
          <article className={`panel notification ${notification.is_read ? "read" : ""}`} key={notification.id}>
            <div>
              <span className="pill">{notification.kind}</span>
              <h2>{notification.title}</h2>
              <p>{notification.message}</p>
            </div>
            {!notification.is_read && (
              <button onClick={() => markRead(notification)}>
                <Check aria-hidden="true" />
                <span>Mark read</span>
              </button>
            )}
          </article>
        ))}
      </div>
    </Page>
  );
}

function Admin() {
  const users = useLoad(api.users);
  const programs = useLoad(api.programs);
  const terms = useLoad(api.terms);
  const instructors = useLoad(api.instructors);
  const hostOrganizations = useLoad(api.hostOrganizations);
  const workflow = useLoad(api.workflowRecords);
  const [programForm, setProgramForm] = useState({ code: "", name: "", description: "" });
  const [termForm, setTermForm] = useState({ name: "", start_date: "", end_date: "", is_active: true });
  const [courseForm, setCourseForm] = useState({ code: "", title: "", description: "", program: "", term: "", instructor: "", capacity: 60, status: "active" });
  const [hostForm, setHostForm] = useState({
    name: "",
    organization_type: "company",
    sector: "",
    address: "",
    contact_person: "",
    contact_email: "",
    contact_phone: "",
    website: "",
    notes: "",
  });
  const [placementForm, setPlacementForm] = useState({
    student: "",
    instructor: "",
    host_organization: "",
    program: "",
    term: "",
    position_title: "",
    department: "",
    start_date: "",
    end_date: "",
    status: "active",
    workplace_supervisor_name: "",
    workplace_supervisor_email: "",
    workplace_supervisor_phone: "",
    learning_objectives: "",
  });

  async function createProgram(event) {
    event.preventDefault();
    await api.createProgram(programForm);
    setProgramForm({ code: "", name: "", description: "" });
    programs.refresh();
  }

  async function createTerm(event) {
    event.preventDefault();
    await api.createTerm(termForm);
    setTermForm({ name: "", start_date: "", end_date: "", is_active: true });
    terms.refresh();
  }

  async function createCourse(event) {
    event.preventDefault();
    await api.createCourse({ ...courseForm, capacity: Number(courseForm.capacity) });
    setCourseForm({ code: "", title: "", description: "", program: "", term: "", instructor: "", capacity: 60, status: "active" });
  }

  async function createHostOrganization(event) {
    event.preventDefault();
    await api.createHostOrganization(hostForm);
    setHostForm({
      name: "",
      organization_type: "company",
      sector: "",
      address: "",
      contact_person: "",
      contact_email: "",
      contact_phone: "",
      website: "",
      notes: "",
    });
    hostOrganizations.refresh();
  }

  async function createPlacement(event) {
    event.preventDefault();
    await api.createPlacement(placementForm);
    setPlacementForm({
      student: "",
      instructor: "",
      host_organization: "",
      program: "",
      term: "",
      position_title: "",
      department: "",
      start_date: "",
      end_date: "",
      status: "active",
      workplace_supervisor_name: "",
      workplace_supervisor_email: "",
      workplace_supervisor_phone: "",
      learning_objectives: "",
    });
  }

  const students = (users.data || []).filter((item) => item.profile?.role === "student");

  return (
    <Page title="Admin Management" subtitle="Academic setup, users, courses, and audit trail.">
      <Status error={users.error || programs.error || terms.error || hostOrganizations.error || workflow.error} loading={users.loading || programs.loading || terms.loading || hostOrganizations.loading} />
      <section className="admin-grid">
        <article className="panel">
          <h2>Host Organizations</h2>
          <form className="compact-form" onSubmit={createHostOrganization}>
            <input placeholder="Host organization name" value={hostForm.name} onChange={(e) => setHostForm({ ...hostForm, name: e.target.value })} required />
            <select value={hostForm.organization_type} onChange={(e) => setHostForm({ ...hostForm, organization_type: e.target.value })}>
              <option value="company">Company</option>
              <option value="ngo">NGO</option>
              <option value="government">Government Office</option>
              <option value="school">School or Institution</option>
              <option value="health">Health Facility</option>
              <option value="other">Other</option>
            </select>
            <input placeholder="Sector" value={hostForm.sector} onChange={(e) => setHostForm({ ...hostForm, sector: e.target.value })} />
            <input placeholder="Contact person" value={hostForm.contact_person} onChange={(e) => setHostForm({ ...hostForm, contact_person: e.target.value })} />
            <input placeholder="Contact email" value={hostForm.contact_email} onChange={(e) => setHostForm({ ...hostForm, contact_email: e.target.value })} />
            <input placeholder="Contact phone" value={hostForm.contact_phone} onChange={(e) => setHostForm({ ...hostForm, contact_phone: e.target.value })} />
            <textarea placeholder="Address" value={hostForm.address} onChange={(e) => setHostForm({ ...hostForm, address: e.target.value })} />
            <textarea placeholder="Notes" value={hostForm.notes} onChange={(e) => setHostForm({ ...hostForm, notes: e.target.value })} />
            <button><Plus aria-hidden="true" /><span>Add host organization</span></button>
          </form>
          {(hostOrganizations.data || []).map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.name}</strong>
              <span>{item.organization_type} - {item.contact_person || "No contact person"}</span>
            </div>
          ))}
        </article>
        <article className="panel">
          <h2>Create Internship Placement</h2>
          <form className="compact-form" onSubmit={createPlacement}>
            <select value={placementForm.student} onChange={(e) => setPlacementForm({ ...placementForm, student: e.target.value })} required>
              <option value="">Student</option>
              {students.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}
            </select>
            <select value={placementForm.instructor} onChange={(e) => setPlacementForm({ ...placementForm, instructor: e.target.value })} required>
              <option value="">Instructor</option>
              {(instructors.data || []).map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}
            </select>
            <select value={placementForm.host_organization} onChange={(e) => setPlacementForm({ ...placementForm, host_organization: e.target.value })} required>
              <option value="">Host organization</option>
              {(hostOrganizations.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <select value={placementForm.program} onChange={(e) => setPlacementForm({ ...placementForm, program: e.target.value })} required>
              <option value="">Program</option>
              {(programs.data || []).map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}
            </select>
            <select value={placementForm.term} onChange={(e) => setPlacementForm({ ...placementForm, term: e.target.value })} required>
              <option value="">Term</option>
              {(terms.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <input placeholder="Position title" value={placementForm.position_title} onChange={(e) => setPlacementForm({ ...placementForm, position_title: e.target.value })} required />
            <input placeholder="Department" value={placementForm.department} onChange={(e) => setPlacementForm({ ...placementForm, department: e.target.value })} />
            <input type="date" value={placementForm.start_date} onChange={(e) => setPlacementForm({ ...placementForm, start_date: e.target.value })} required />
            <input type="date" value={placementForm.end_date} onChange={(e) => setPlacementForm({ ...placementForm, end_date: e.target.value })} required />
            <input placeholder="Workplace supervisor name" value={placementForm.workplace_supervisor_name} onChange={(e) => setPlacementForm({ ...placementForm, workplace_supervisor_name: e.target.value })} />
            <input placeholder="Workplace supervisor email" value={placementForm.workplace_supervisor_email} onChange={(e) => setPlacementForm({ ...placementForm, workplace_supervisor_email: e.target.value })} />
            <input placeholder="Workplace supervisor phone" value={placementForm.workplace_supervisor_phone} onChange={(e) => setPlacementForm({ ...placementForm, workplace_supervisor_phone: e.target.value })} />
            <textarea placeholder="Learning objectives" value={placementForm.learning_objectives} onChange={(e) => setPlacementForm({ ...placementForm, learning_objectives: e.target.value })} />
            <button><Plus aria-hidden="true" /><span>Create placement</span></button>
          </form>
        </article>
        <article className="panel">
          <h2>Programs</h2>
          <form className="compact-form" onSubmit={createProgram}>
            <input placeholder="Code" value={programForm.code} onChange={(e) => setProgramForm({ ...programForm, code: e.target.value })} required />
            <input placeholder="Program name" value={programForm.name} onChange={(e) => setProgramForm({ ...programForm, name: e.target.value })} required />
            <textarea placeholder="Description" value={programForm.description} onChange={(e) => setProgramForm({ ...programForm, description: e.target.value })} />
            <button>
              <Plus aria-hidden="true" />
              <span>Add program</span>
            </button>
          </form>
          {(programs.data || []).map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.code}</strong>
              <span>{item.name}</span>
            </div>
          ))}
        </article>
        <article className="panel">
          <h2>Terms</h2>
          <form className="compact-form" onSubmit={createTerm}>
            <input placeholder="Term name" value={termForm.name} onChange={(e) => setTermForm({ ...termForm, name: e.target.value })} required />
            <input type="date" value={termForm.start_date} onChange={(e) => setTermForm({ ...termForm, start_date: e.target.value })} required />
            <input type="date" value={termForm.end_date} onChange={(e) => setTermForm({ ...termForm, end_date: e.target.value })} required />
            <label className="checkline">
              <input type="checkbox" checked={termForm.is_active} onChange={(e) => setTermForm({ ...termForm, is_active: e.target.checked })} />
              Active
            </label>
            <button>
              <Plus aria-hidden="true" />
              <span>Add term</span>
            </button>
          </form>
          {(terms.data || []).map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.name}</strong>
              <span>{item.start_date} to {item.end_date}</span>
            </div>
          ))}
        </article>
        <article className="panel">
          <h2>Create Course</h2>
          <form className="compact-form" onSubmit={createCourse}>
            <input placeholder="Code" value={courseForm.code} onChange={(e) => setCourseForm({ ...courseForm, code: e.target.value })} required />
            <input placeholder="Title" value={courseForm.title} onChange={(e) => setCourseForm({ ...courseForm, title: e.target.value })} required />
            <textarea placeholder="Description" value={courseForm.description} onChange={(e) => setCourseForm({ ...courseForm, description: e.target.value })} />
            <select value={courseForm.program} onChange={(e) => setCourseForm({ ...courseForm, program: e.target.value })} required>
              <option value="">Program</option>
              {(programs.data || []).map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}
            </select>
            <select value={courseForm.term} onChange={(e) => setCourseForm({ ...courseForm, term: e.target.value })} required>
              <option value="">Term</option>
              {(terms.data || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <select value={courseForm.instructor} onChange={(e) => setCourseForm({ ...courseForm, instructor: e.target.value })} required>
              <option value="">Instructor</option>
              {(instructors.data || []).map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}
            </select>
            <input type="number" min="1" value={courseForm.capacity} onChange={(e) => setCourseForm({ ...courseForm, capacity: e.target.value })} />
            <button>
              <Plus aria-hidden="true" />
              <span>Create course</span>
            </button>
          </form>
        </article>
        <article className="panel">
          <h2>Users</h2>
          {(users.data || []).map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.username}</strong>
              <span>{item.profile?.role || "student"} - {item.email}</span>
            </div>
          ))}
        </article>
        <article className="panel span-two">
          <h2>Workflow Audit</h2>
          {(workflow.data || []).slice(0, 12).map((item) => (
            <div className="list-row" key={item.id}>
              <strong>{item.action}</strong>
              <span>{item.actor_detail?.display_name || "System"} - {new Date(item.created_at).toLocaleString()}</span>
            </div>
          ))}
        </article>
      </section>
    </Page>
  );
}

function Page({ title, subtitle, children }) {
  return (
    <>
      <div className="page-head">
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children}
    </>
  );
}

function Status({ error, loading }) {
  if (loading) return <p className="muted">Loading...</p>;
  if (error) return <p className="error">{error}</p>;
  return null;
}

function ListEmpty({ items, label }) {
  if (items.length) return null;
  return <p className="muted">{label}</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
      <Route path="/internship" element={<Navigate to="/app/internship" replace />} />
      <Route path="/logbook" element={<Navigate to="/app/logbook" replace />} />
      <Route path="/evaluations" element={<Navigate to="/app/evaluations" replace />} />
      <Route path="/courses" element={<Navigate to="/app/courses" replace />} />
      <Route path="/assignments" element={<Navigate to="/app/assignments" replace />} />
      <Route path="/notifications" element={<Navigate to="/app/notifications" replace />} />
      <Route path="/password" element={<Navigate to="/app/password" replace />} />
      <Route
        path="/app/*"
        element={
          <Protected>
            <Shell />
          </Protected>
        }
      />
    </Routes>
  );
}
