type CacheEntry<T> = {
  expiresAt: number;
  value: T;
};

const cache = new Map<string, CacheEntry<unknown>>();

export async function fetchWithCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  opts?: { ttlMs?: number; force?: boolean }
): Promise<T> {
  const ttlMs = opts?.ttlMs ?? 10_000;
  const force = opts?.force ?? false;
  const now = Date.now();
  if (!force) {
    const hit = cache.get(key) as CacheEntry<T> | undefined;
    if (hit && hit.expiresAt > now) {
      return hit.value;
    }
  }
  const value = await fetcher();
  cache.set(key, { value, expiresAt: now + ttlMs });
  return value;
}

export function invalidateCache(prefix?: string): void {
  if (!prefix) {
    cache.clear();
    return;
  }
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) {
      cache.delete(key);
    }
  }
}
