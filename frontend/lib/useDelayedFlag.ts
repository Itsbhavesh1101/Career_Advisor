import { useEffect, useState } from "react";

export function useDelayedFlag(active: boolean, delayMs = 7000): boolean {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!active) {
      setVisible(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setVisible(true);
    }, delayMs);

    return () => window.clearTimeout(timer);
  }, [active, delayMs]);

  return visible;
}
