import express from "express";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema"; // CORREGIDO: Importar de './schema' (TypeScript resolverá el .ts)
import { eq } from "drizzle-orm";
import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import dotenv from "dotenv";
import cors from "cors"; // Añadido para habilitar CORS

dotenv.config();

const app = express();
app.use(express.json());
app.use(cors()); // Usar el middleware CORS

// Conexión a la base de datos
const connection = postgres(process.env.DATABASE_URL!);
const db = drizzle(connection, { schema });

// Extender la interfaz Request de Express para incluir 'user'
declare global {
  namespace Express {
    interface Request {
      user?: { id: string; username: string };
    }
  }
}

// Middleware de autenticación
const authenticateToken = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const token = req.headers["authorization"]?.split(" ")[1];
  if (!token) return res.status(401).json({ error: "Token requerido" });

  jwt.verify(token, process.env.JWT_SECRET!, (err: any, user: any) => {
    if (err) return res.status(403).json({ error: "Token inválido" });
    req.user = user; // Asigna la información del usuario al objeto request
    next();
  });
};

// Ruta /api/signup (Crear usuario)
app.post("/api/signup", async (req, res) => {
  // Validar con Zod
  const parsedUser = schema.insertUserSchema.safeParse(req.body);

  if (!parsedUser.success) {
    return res.status(400).json({ errors: parsedUser.error.errors });
  }

  const { username, email, password } = parsedUser.data;
  const hashedPassword = await bcrypt.hash(password, 10);

  try {
    const result = await db
      .insert(schema.users)
      .values({ username, email, passwordHash: hashedPassword })
      .returning();
    res.status(201).json({ message: "Usuario creado", user: result[0] });
  } catch (err: any) {
    // Manejo de errores específicos (ej. usuario ya existe)
    if (err.message.includes("duplicate key value violates unique constraint")) {
      return res.status(409).json({ error: "El nombre de usuario o email ya existe." });
    }
    res.status(500).json({ error: err.message });
  }
});

// Ruta /api/login (Iniciar sesión)
app.post("/api/login", async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ error: "Usuario y contraseña requeridos" });
  }
  try {
    const [user] = await db
      .select()
      .from(schema.users)
      .where(eq(schema.users.username, username));

    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      return res.status(401).json({ error: "Credenciales inválidas" });
    }

    const token = jwt.sign(
      { id: user.id, username: user.username },
      process.env.JWT_SECRET!,
      { expiresIn: "1h" }
    );
    res.json({ token });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Ruta protegida de ejemplo para animals (obtener animales del usuario)
app.get("/api/animals", authenticateToken, async (req, res) => {
  try {
    if (!req.user || !req.user.id) {
      return res.status(401).json({ error: "Usuario no autenticado." });
    }
    const animals = await db
      .select()
      .from(schema.animals)
      .where(eq(schema.animals.userId, req.user.id));
    res.json(animals);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

// Añadir una nueva ruta para crear un animal (ejemplo)
app.post("/api/animals", authenticateToken, async (req, res) => {
  try {
    if (!req.user || !req.user.id) {
      return res.status(401).json({ error: "Usuario no autenticado." });
    }

    const parsedAnimal = schema.insertAnimalSchema.safeParse(req.body);

    if (!parsedAnimal.success) {
      return res.status(400).json({ errors: parsedAnimal.error.errors });
    }

    // Asignar el userId del token al nuevo animal
    const newAnimal = { ...parsedAnimal.data, userId: req.user.id };

    const result = await db.insert(schema.animals).values(newAnimal).returning();
    res.status(201).json({ message: "Animal creado exitosamente", animal: result[0] });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});


// Iniciar el servidor
app.listen(5001, () => console.log("Server running on port 5001"));