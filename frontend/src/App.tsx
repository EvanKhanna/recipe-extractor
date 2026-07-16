import { useCallback, useEffect, useState } from "react";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
  useAuth,
} from "@clerk/clerk-react";
import { listRecipes, type Recipe, type TokenGetter } from "./lib/api";
import AddRecipe from "./components/AddRecipe";
import RecipeList from "./components/RecipeList";

function Cookbook({ getToken }: { getToken: TokenGetter }) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRecipes(await listRecipes(getToken));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <>
      <AddRecipe getToken={getToken} onAdded={refresh} />
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="muted">Loading your cookbook…</p>
      ) : (
        <RecipeList recipes={recipes} getToken={getToken} onChange={refresh} />
      )}
    </>
  );
}

// Wraps Cookbook with the real Clerk session-token getter.
function ClerkedCookbook() {
  const { getToken } = useAuth();
  return <Cookbook getToken={getToken} />;
}

export default function App({ disableAuth = false }: { disableAuth?: boolean }) {
  if (disableAuth) {
    // No Clerk provider in the tree — never call Clerk hooks here.
    const getToken: TokenGetter = async () => null;
    return (
      <div className="app">
        <header className="topbar">
          <h1>🍳 Recipe Extractor</h1>
          <span className="chip">Dev mode · no auth</span>
        </header>
        <main className="container">
          <Cookbook getToken={getToken} />
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>🍳 Recipe Extractor</h1>
        <div>
          <SignedIn>
            <UserButton />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <button className="primary">Sign in</button>
            </SignInButton>
          </SignedOut>
        </div>
      </header>

      <main className="container">
        <SignedOut>
          <div className="hero">
            <h2>Save any recipe from a Reel, TikTok, or photo.</h2>
            <p className="muted">
              Sign in to turn cooking videos and images into clean, structured
              recipes you can keep forever.
            </p>
          </div>
        </SignedOut>
        <SignedIn>
          <ClerkedCookbook />
        </SignedIn>
      </main>
    </div>
  );
}
