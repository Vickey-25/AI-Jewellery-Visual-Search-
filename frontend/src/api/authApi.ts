import type { AuthResponse, LoginPayload, RegisterPayload, User } from "../types/auth";
import { request } from "./client";

export function loginApi(payload: LoginPayload, signal?: AbortSignal) {
  return request<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}

export function registerApi(payload: RegisterPayload, signal?: AbortSignal) {
  return request<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}

export function getMeApi(signal?: AbortSignal) {
  return request<User>("/api/v1/auth/me", { signal });
}
