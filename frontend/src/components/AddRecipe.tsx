import { useState } from "react";
import { createFromImage, createFromUrl, type TokenGetter } from "../lib/api";

interface Props {
  getToken: TokenGetter;
  onAdded: () => void;
}

type Mode = "url" | "image";

export default function AddRecipe({ getToken, onAdded }: Props) {
  const [mode, setMode] = useState<Mode>("url");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "url") {
        if (!url.trim()) throw new Error("Please paste a TikTok or Reel URL.");
        await createFromUrl(getToken, url.trim());
        setUrl("");
      } else {
        if (!file) throw new Error("Please choose an image.");
        await createFromImage(getToken, file);
        setFile(null);
      }
      onAdded();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card add-recipe">
      <div className="tabs">
        <button
          className={mode === "url" ? "tab active" : "tab"}
          onClick={() => setMode("url")}
          type="button"
        >
          From video URL
        </button>
        <button
          className={mode === "image" ? "tab active" : "tab"}
          onClick={() => setMode("image")}
          type="button"
        >
          From image
        </button>
      </div>

      <form onSubmit={submit}>
        {mode === "url" ? (
          <input
            type="url"
            placeholder="https://www.tiktok.com/...  or  https://www.instagram.com/reel/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={busy}
          />
        ) : (
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={busy}
          />
        )}

        <button className="primary" type="submit" disabled={busy}>
          {busy ? "Extracting…" : "Extract recipe"}
        </button>
      </form>

      {busy && (
        <p className="muted small">
          Downloading, transcribing, and asking Claude to write the recipe. Video
          transcription can take a little while.
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
