import { useCallback, useRef, useState } from "react";

export function useForm<T extends object>(initial: T) {
  const initialRef = useRef(initial);
  const [values, setValues] = useState<T>(initialRef.current);
  const [loading, setLoading] = useState(false);

  const handleChange = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setValues(
      (prev) =>
        ({
          ...prev,
          [key]: value,
        }) as T,
    );
  }, []);

  const reset = useCallback(() => {
    setValues(initialRef.current);
  }, []);

  return {
    values,
    handleChange,
    loading,
    setLoading,
    reset,
  };
}
