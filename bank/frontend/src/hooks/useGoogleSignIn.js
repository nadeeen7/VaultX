import { useEffect, useRef, useCallback } from "react";

/**
 * Custom hook to load the Google Identity Services library and provide
 * a function to trigger the Google Sign-In popup.
 *
 * Usage:
 *   const { googleSignIn, isLoaded } = useGoogleSignIn(handleCredentialResponse);
 */
export function useGoogleSignIn(onCredentialResponse) {
  const googleRef = useRef(null);
  const callbackRef = useRef(onCredentialResponse);

  // Keep callback ref fresh without re-rendering the script loader
  useEffect(() => {
    callbackRef.current = onCredentialResponse;
  }, [onCredentialResponse]);

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) return;

    // Prevent loading the script twice
    if (document.getElementById("google-identity-services")) {
      // Script already loaded — just reinitialize
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => callbackRef.current(response),
        });
      }
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.id = "google-identity-services";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response) => callbackRef.current(response),
        });
      }
    };
    document.head.appendChild(script);
  }, []);

  const googleSignIn = useCallback(() => {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
    }
  }, []);

  const isLoaded = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);

  return { googleSignIn, isLoaded };
}
