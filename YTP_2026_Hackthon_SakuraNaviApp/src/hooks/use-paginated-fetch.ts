import { DependencyList, useCallback, useEffect, useState } from "react";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

type FetchPageFn<T> = (params: {
  offset: number;
  limit: number;
}) => Promise<PaginatedResponse<T>>;

export function usePaginatedFetch<T>(
  fetchFn: FetchPageFn<T>,
  deps: DependencyList,
  pageSize = 10,
) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  const load = useCallback(
    async (nextOffset: number, append: boolean) => {
      setLoading(true);
      try {
        const result = await fetchFn({
          offset: nextOffset,
          limit: pageSize,
        });

        setItems((prev) =>
          append ? [...prev, ...result.items] : result.items,
        );
        setTotal(result.total);
        setOffset(nextOffset);
      } finally {
        setLoading(false);
      }
    },
    [fetchFn, pageSize],
  );

  const reload = useCallback(async () => {
    await load(0, false);
  }, [load]);

  const hasMore = items.length < total;

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) {
      return;
    }

    await load(offset + pageSize, true);
  }, [hasMore, load, loading, offset, pageSize]);

  useEffect(() => {
    void reload();
  }, [reload, ...deps]);

  return {
    items,
    loading,
    total,
    loadMore,
    reload,
    hasMore,
  };
}
