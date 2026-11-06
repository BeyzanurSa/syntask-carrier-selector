"use client";

import { useEffect, useId, useState } from "react";

import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/client";

type Check = { known: boolean; normalized: string; suggestion: string | null };

// Loaded once per page and shared by every CityInput on it.
let knownCitiesPromise: Promise<string[]> | null = null;
function loadKnownCities(): Promise<string[]> {
  knownCitiesPromise ??= api
    .GET("/cities")
    .then(({ data }) => data ?? [])
    .catch(() => {
      knownCitiesPromise = null; // retry on the next mount if the backend was down
      return [];
    });
  return knownCitiesPromise;
}

/**
 * A city field that suggests known cities while typing and, on blur, asks the backend whether the
 * name is known. A likely typo gets a "did you mean" button; a new city only gets a note, because
 * an unknown city is still allowed (its distance comes from the distance API).
 */
export function CityInput({
  id,
  value,
  onChange,
  required,
  placeholder,
  invalid,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  placeholder?: string;
  invalid?: boolean;
}) {
  const listId = useId();
  const [cities, setCities] = useState<string[]>([]);
  const [check, setCheck] = useState<Check | null>(null);

  useEffect(() => {
    loadKnownCities().then(setCities);
  }, []);

  async function runCheck() {
    const name = value.trim();
    if (!name) {
      setCheck(null);
      return;
    }
    try {
      const { data } = await api.GET("/cities/check", { params: { query: { name } } });
      setCheck(data ?? null);
    } catch {
      setCheck(null);
    }
  }

  return (
    <>
      <Input
        id={id}
        list={listId}
        required={required}
        placeholder={placeholder}
        autoComplete="off"
        aria-invalid={invalid || undefined}
        aria-describedby={check && !check.known ? `${id}-check` : undefined}
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setCheck(null);
        }}
        onBlur={runCheck}
      />
      <datalist id={listId}>
        {cities.map((city) => (
          <option key={city} value={city} />
        ))}
      </datalist>
      {check && !check.known && (
        <p id={`${id}-check`} className="text-xs" aria-live="polite">
          {check.suggestion ? (
            <>
              <span className="text-muted-foreground">Listede yok. </span>
              <button
                type="button"
                className="text-primary font-medium underline-offset-4 hover:underline"
                onClick={() => {
                  onChange(check.suggestion!);
                  setCheck({ known: true, normalized: check.suggestion!, suggestion: null });
                }}
              >
                {check.suggestion} mi demek istediniz?
              </button>
            </>
          ) : (
            <span className="text-muted-foreground">
              {check.normalized} listede yok; mesafesi mesafe API&apos;sinden aranacak.
            </span>
          )}
        </p>
      )}
    </>
  );
}
