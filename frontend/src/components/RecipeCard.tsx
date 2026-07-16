import { useState } from "react";
import { deleteRecipe, type Recipe, type TokenGetter } from "../lib/api";

interface Props {
  recipe: Recipe;
  getToken: TokenGetter;
  onChange: () => void;
}

export default function RecipeCard({ recipe, getToken, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function remove() {
    if (!confirm(`Delete "${recipe.title}"?`)) return;
    setDeleting(true);
    try {
      await deleteRecipe(getToken, recipe.id);
      onChange();
    } finally {
      setDeleting(false);
    }
  }

  const meta = [
    recipe.servings,
    recipe.prep_time && `Prep ${recipe.prep_time}`,
    recipe.cook_time && `Cook ${recipe.cook_time}`,
  ].filter(Boolean);

  return (
    <article className="card recipe">
      <div className="recipe-head" onClick={() => setOpen(!open)}>
        <div>
          <h3>{recipe.title}</h3>
          {meta.length > 0 && <p className="muted small">{meta.join(" · ")}</p>}
        </div>
        <span className="chip">{recipe.source_type}</span>
      </div>

      {recipe.description && <p className="desc">{recipe.description}</p>}

      {open && (
        <div className="recipe-body">
          <h4>Ingredients</h4>
          <ul>
            {recipe.ingredients.map((ing, i) => (
              <li key={i}>
                {ing.quantity ? <strong>{ing.quantity} </strong> : null}
                {ing.item}
              </li>
            ))}
          </ul>

          <h4>Steps</h4>
          <ol>
            {recipe.steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>

          <div className="recipe-footer">
            {recipe.source_url && (
              <a href={recipe.source_url} target="_blank" rel="noreferrer">
                Original post ↗
              </a>
            )}
            <button className="danger" onClick={remove} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete"}
            </button>
          </div>
        </div>
      )}

      {!open && (
        <button className="link" onClick={() => setOpen(true)}>
          Show recipe
        </button>
      )}
    </article>
  );
}
