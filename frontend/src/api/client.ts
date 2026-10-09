import { API_BASE_URL } from "../config";

export type ApiErrorKind =
  | "network"
  | "timeout"
  | "invalid-image"
  | "unavailable"
  | "not-found"
  | "server"
  | "aborted"
  | "unknown";

/** An error whose `message` is always safe to show to a customer. */
export class ApiError extends Error {
  kind: ApiErrorKind;
  status: number;
  code: string;

  constructor(kind: ApiErrorKind, message: string, status = 0, code = "") {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.code = code;
  }
}

const BY_CODE: Record<string, { kind: ApiErrorKind; message: string }> = {
  INVALID_IMAGE: {
    kind: "invalid-image",
    message: "We couldn't read that image. Please try a clear JPG, PNG or WebP photo of jewellery.",
  },
  UNSUPPORTED_FORMAT: {
    kind: "invalid-image",
    message: "That file type isn't supported. Please use a JPG, PNG or WebP image.",
  },
  IMAGE_TOO_LARGE: {
    kind: "invalid-image",
    message: "That image is too large. Please choose one under 5 MB.",
  },
  FAISS_UNAVAILABLE: {
    kind: "unavailable",
    message: "Visual search is getting ready. Please try again in a moment.",
  },
  AI_UNAVAILABLE: {
    kind: "unavailable",
    message: "Visual search is getting ready. Please try again in a moment.",
  },
  DATABASE_UNAVAILABLE: {
    kind: "unavailable",
    message: "Our collection is temporarily unavailable. Please try again shortly.",
  },
  VALIDATION_ERROR: {
    kind: "unknown",
    message: "Something about that search wasn't quite right. Please adjust it and try again.",
  },
  INVALID_REQUEST: {
    kind: "unknown",
    message: "Please add an image, a few words, or both.",
  },
  PRODUCT_NOT_FOUND: { kind: "not-found", message: "We couldn't find that piece in the collection." },
  PRODUCT_NOT_INDEXED: {
    kind: "not-found",
    message: "Similar pieces aren't available for this design yet.",
  },
};

export const isAbortError = (e: unknown): boolean => e instanceof ApiError && e.kind === "aborted";

export function toApiError(e: unknown): ApiError {
  return e instanceof ApiError
    ? e
    : new ApiError("unknown", "Something went wrong. Please try again.");
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: BodyInit | null;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  /** CPU-based AI can be slow, so the default is generous. */
  timeoutMs?: number;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body = null, headers = {}, signal, timeoutMs = 90_000 } = options;
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const forwardAbort = () => controller.abort();
  signal?.addEventListener("abort", forwardAbort);
  if (signal?.aborted) controller.abort();

  const reqHeaders: Record<string, string> = { ...headers };
  const token = localStorage.getItem("lumiere_token");
  if (token && !reqHeaders["Authorization"]) {
    reqHeaders["Authorization"] = `Bearer ${token}`;
  }

  try {
    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${path}`, { method, body, headers: reqHeaders, signal: controller.signal });
    } catch {
      if (timedOut) {
        throw new ApiError("timeout", "That's taking longer than expected. Please try again.");
      }
      if (signal?.aborted) throw new ApiError("aborted", "Request cancelled.");
      throw new ApiError(
        "network",
        "We couldn't reach the collection. Please check your connection and try again.",
      );
    }

    if (!response.ok) {
      let code = "";
      let backendMessage = "";
      try {
        const payload = (await response.json()) as { error?: { code?: string; message?: string } };
        code = payload.error?.code ?? "";
        backendMessage = payload.error?.message ?? "";
      } catch {
        // non-JSON error body: fall through
      }
      const known = BY_CODE[code];
      const finalMsg = backendMessage || known?.message || "Something went wrong. Please try again.";
      const kind = known?.kind ?? (response.status === 401 || response.status === 403 ? "unavailable" : "unknown");
      throw new ApiError(kind, finalMsg, response.status, code);
    }
    return (await response.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (timedOut) throw new ApiError("timeout", "That's taking longer than expected. Please try again.");
    if (signal?.aborted) throw new ApiError("aborted", "Request cancelled.");
    throw new ApiError("unknown", "Something went wrong. Please try again.");
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", forwardAbort);
  }
}
