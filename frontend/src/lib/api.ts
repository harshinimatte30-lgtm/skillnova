const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('skillnova_token');

  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let res: Response;

  try {
    res = await fetch(`${API}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      `Cannot reach SkillNova API at ${API}. Make sure the FastAPI server is running.`
    );
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);

    let message = `Request failed (${res.status})`;

    if (typeof body?.detail === 'string') {
      message = body.detail;
    } else if (Array.isArray(body?.detail)) {
      message = body.detail
        .map((error: any) => {
          const field = Array.isArray(error.loc)
            ? error.loc.filter((x: any) => x !== 'body').join('.')
            : 'field';

          return `${field}: ${error.msg}`;
        })
        .join(', ');
    }

    throw new Error(message);
  }

  return res.json();
}