import React from "react";
import ReactDOM from "react-dom/client";
import { ClerkProvider } from "@clerk/clerk-react";
import App from "./App";
import "./index.css";

// Dev-only bypass: when VITE_DISABLE_AUTH=true we skip Clerk entirely and run
// the app as a single fixed user. Pair with DISABLE_AUTH=true on the backend.
const disableAuth = import.meta.env.VITE_DISABLE_AUTH === "true";
const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

const root = ReactDOM.createRoot(document.getElementById("root")!);

if (disableAuth) {
  root.render(
    <React.StrictMode>
      <App disableAuth />
    </React.StrictMode>
  );
} else {
  if (!publishableKey) {
    throw new Error(
      "Missing VITE_CLERK_PUBLISHABLE_KEY. Add it to your .env (see .env.example), " +
        "or set VITE_DISABLE_AUTH=true to run without Clerk in development."
    );
  }
  root.render(
    <React.StrictMode>
      <ClerkProvider publishableKey={publishableKey}>
        <App />
      </ClerkProvider>
    </React.StrictMode>
  );
}
