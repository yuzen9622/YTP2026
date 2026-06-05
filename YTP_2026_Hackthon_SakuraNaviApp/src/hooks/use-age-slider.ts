import { useCallback, useState } from "react";

const MIN_AGE = 0;
const MAX_AGE = 150;

function clampAge(value: number) {
  return Math.min(MAX_AGE, Math.max(MIN_AGE, Math.round(value)));
}

export function useAgeSlider(initial = 25) {
  const [age, setAge] = useState(clampAge(initial));

  const handleValueChange = useCallback((value: number) => {
    setAge(clampAge(value));
  }, []);

  return {
    age,
    handleValueChange,
  };
}
