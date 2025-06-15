// src/types/index.ts
export interface Finca {
  id: number;
  user_id: number; // Añadido para reflejar la relación con users
  name: string;
  location: string;
  // Opcional: Añade propiedades adicionales si la API las devuelve (e.g., createdAt)
  // createdAt?: string;
}