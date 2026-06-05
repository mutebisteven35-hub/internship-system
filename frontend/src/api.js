const DEFAULT_API_BASE_URL = import.meta.env.DEV ? "http://127.0.0.1:8000/api" : "/api";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

export function getToken() {
  return localStorage.getItem("iles_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("iles_token", token);
  } else {
    localStorage.removeItem("iles_token");
  }
}

export async function apiRequest(path, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Token ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body:
      options.body && !(options.body instanceof FormData) && typeof options.body !== "string"
        ? JSON.stringify(options.body)
        : options.body,
  });

  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || Object.values(data).flat().join(" ") || "Request failed";
    throw new Error(message);
  }
  return data;
}

export const api = {
  login: (username, password) => apiRequest("/auth/login/", { method: "POST", body: { username, password } }),
  logout: () => apiRequest("/auth/logout/", { method: "POST" }),
  changePassword: (body) => apiRequest("/auth/change-password/", { method: "POST", body }),
  requestPasswordReset: (body) => apiRequest("/auth/password-reset/request/", { method: "POST", body }),
  confirmPasswordReset: (body) => apiRequest("/auth/password-reset/confirm/", { method: "POST", body }),
  me: () => apiRequest("/me/"),
  dashboard: () => apiRequest("/dashboard/"),
  users: () => apiRequest("/users/"),
  instructors: () => apiRequest("/users/instructors/"),
  programs: () => apiRequest("/programs/"),
  terms: () => apiRequest("/terms/"),
  courses: () => apiRequest("/courses/"),
  course: (id) => apiRequest(`/courses/${id}/`),
  hostOrganizations: () => apiRequest("/host-organizations/"),
  placements: () => apiRequest("/internship-placements/"),
  logbookEntries: () => apiRequest("/logbook-entries/"),
  attendanceRecords: () => apiRequest("/attendance-records/"),
  internshipEvaluations: () => apiRequest("/internship-evaluations/"),
  registerCourse: (id) => apiRequest(`/courses/${id}/register/`, { method: "POST" }),
  enrollments: () => apiRequest("/enrollments/"),
  approveEnrollment: (id) => apiRequest(`/enrollments/${id}/approve/`, { method: "POST" }),
  rejectEnrollment: (id) => apiRequest(`/enrollments/${id}/reject/`, { method: "POST" }),
  materials: () => apiRequest("/materials/"),
  assignments: () => apiRequest("/assignments/"),
  submissions: () => apiRequest("/submissions/"),
  notifications: () => apiRequest("/notifications/"),
  workflowRecords: () => apiRequest("/workflow-records/"),
  createProgram: (body) => apiRequest("/programs/", { method: "POST", body }),
  createTerm: (body) => apiRequest("/terms/", { method: "POST", body }),
  createCourse: (body) => apiRequest("/courses/", { method: "POST", body }),
  createHostOrganization: (body) => apiRequest("/host-organizations/", { method: "POST", body }),
  createPlacement: (body) => apiRequest("/internship-placements/", { method: "POST", body }),
  createLogbookEntry: (body) => apiRequest("/logbook-entries/", { method: "POST", body }),
  submitLogbookEntry: (id) => apiRequest(`/logbook-entries/${id}/submit/`, { method: "POST" }),
  reviewLogbookEntry: (id, body) => apiRequest(`/logbook-entries/${id}/review/`, { method: "POST", body }),
  createAttendanceRecord: (body) => apiRequest("/attendance-records/", { method: "POST", body }),
  createInternshipEvaluation: (body) => apiRequest("/internship-evaluations/", { method: "POST", body }),
  createMaterial: (body) => apiRequest("/materials/", { method: "POST", body }),
  createAssignment: (body) => apiRequest("/assignments/", { method: "POST", body }),
  createSubmission: (body) => apiRequest("/submissions/", { method: "POST", body }),
  gradeSubmission: (id, body) => apiRequest(`/submissions/${id}/grade/`, { method: "POST", body }),
  markNotificationRead: (id) => apiRequest(`/notifications/${id}/mark_read/`, { method: "POST" }),
};
