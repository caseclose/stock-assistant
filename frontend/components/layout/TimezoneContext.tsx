"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DEFAULT_TIMEZONE,
  loadStoredTimezone,
  storeTimezone,
  timezoneLabel,
  type DisplayTimezone,
} from "@/lib/timezone";

type TimezoneContextValue = {
  timezone: DisplayTimezone;
  setTimezone: (tz: DisplayTimezone) => void;
  label: string;
};

const TimezoneContext = createContext<TimezoneContextValue | null>(null);

export function TimezoneProvider({ children }: { children: ReactNode }) {
  const [timezone, setTimezoneState] = useState<DisplayTimezone>(DEFAULT_TIMEZONE);

  useEffect(() => {
    setTimezoneState(loadStoredTimezone());
  }, []);

  const setTimezone = useCallback((tz: DisplayTimezone) => {
    setTimezoneState(tz);
    storeTimezone(tz);
  }, []);

  const value = useMemo(
    () => ({
      timezone,
      setTimezone,
      label: timezoneLabel(timezone),
    }),
    [timezone, setTimezone],
  );

  return (
    <TimezoneContext.Provider value={value}>{children}</TimezoneContext.Provider>
  );
}

export function useTimezone() {
  const ctx = useContext(TimezoneContext);
  if (!ctx) {
    throw new Error("useTimezone must be used within TimezoneProvider");
  }
  return ctx;
}
