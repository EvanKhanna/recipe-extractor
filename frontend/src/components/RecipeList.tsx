import { type Recipe, type TokenGetter } from "../lib/api";
import RecipeCard from "./RecipeCard";

interface Props {
  recipes: Recipe[];
  getToken: TokenGetter;
  onChange: () => void;
}

export default function RecipeList({ recipes, getToken, onChange }: Props) {
  if (recipes.length === 0) {
    return (
      <p className="muted empty">
        No recipes yet. Paste a cooking video URL or upload a photo above to get
        started.
      </p>
    );
  }

  return (
    <section className="recipe-list">
      {recipes.map((r) => (
        <RecipeCard key={r.id} recipe={r} getToken={getToken} onChange={onChange} />
      ))}
    </section>
  );
}
