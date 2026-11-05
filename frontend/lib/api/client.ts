import createClient from "openapi-fetch";

import type { paths } from "./schema";

// Only the backend URL lives on the frontend. No secrets here.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl: API_BASE_URL });
