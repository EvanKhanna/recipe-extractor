const BASE = import.meta.env.VITE_API_URL || "/api";

export interface Ingredient {
  quantity: string | null;
  item: string;
}

export interface Recipe {
  id: number;
  title: string;
  description: string | null;
  ingredients: Ingredient[];
  steps: string[];
  servings: string | null;
  prep_time: string | null;
  cook_time: string | null;
  source_type: string;
  source_url: string | null;
  created_at: string;
}

/** A function that returns the current Clerk session token (or null). */
export type TokenGetter = () => Promise<string | null>;

async function authHeaders(getToken: TokenGetter): Promise<HeadersInit> {
  const token = await getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle(res: Response): Promise<any> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function listRecipes(getToken: TokenGetter): Promise<Recipe[]> {
  const res = await fetch(`${BASE}/recipes`, {
    headers: await authHeaders(getToken),
  });
  return handle(res);
}

export async function createFromUrl(
  getToken: TokenGetter,
  url: string
): Promise<Recipe> {
  const res = await fetch(`${BASE}/recipes/from-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders(getToken)),
    },
    body: JSON.stringify({ url }),
  });
  return handle(res);
}

export async function createFromImage(
  getToken: TokenGetter,
  file: File
): Promise<Recipe> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/recipes/from-image`, {
    method: "POST",
    headers: await authHeaders(getToken),
    body: form,
  });
  return handle(res);
}

export async function deleteRecipe(
  getToken: TokenGetter,
  id: number
): Promise<void> {
  const res = await fetch(`${BASE}/recipes/${id}`, {
    method: "DELETE",
    headers: await authHeaders(getToken),
  });
  await handle(res);
}
