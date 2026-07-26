export type Chat = { id: string; title: string; created_at: string };
export type Message = {
  id: string;
  role: string;
  content: string;
  agent_metadata: { intent: string; steps: string[]; actions?: { tasks_created?: number; trip_created?: string; reminder_created?: string } } | null;
  created_at: string;
};
export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  due_date: string | null;
  created_at: string;
};
export type Trip = {
  id: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  budget: number | null;
  status: string;
};
export type Reminder = {
  id: string;
  title: string;
  remind_at: string;
  is_sent: boolean;
};
export type CurrentUser = { id: string; email: string; full_name: string | null; is_active: boolean };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    let errorMsg = "Request failed";
    if (typeof body.detail === "string") {
      errorMsg = body.detail;
    } else if (Array.isArray(body.detail)) {
      errorMsg = body.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
    } else if (body.detail) {
      errorMsg = JSON.stringify(body.detail);
    }
    throw new ApiError(response.status, errorMsg);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  register: (email: string, password: string, fullName?: string) =>
    request<CurrentUser>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getMe: (token: string) => request<CurrentUser>("/auth/me", {}, token),

  listChats: (token: string) => request<Chat[]>("/chats", {}, token),

  createChat: (token: string) => request<Chat>("/chats", { method: "POST" }, token),

  sendMessage: (token: string, chatId: string, content: string) =>
    request<Message>(`/chats/${chatId}/messages`, { method: "POST", body: JSON.stringify({ content }) }, token),

  listTasks: (token: string) => request<Task[]>("/tasks", {}, token),

  updateTaskStatus: (token: string, taskId: string, status: string) =>
    request<Task>(`/tasks/${taskId}/status`, { method: "PATCH", body: JSON.stringify({ status }) }, token),

  listTrips: (token: string) => request<Trip[]>("/trips", {}, token),

  listReminders: (token: string) => request<Reminder[]>("/reminders", {}, token),
};

export { ApiError };
