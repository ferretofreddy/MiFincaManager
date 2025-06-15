import { pgTable, serial, text, integer, date, timestamp, uniqueIndex, uuid } from "drizzle-orm/pg-core";
import { relations, sql } from "drizzle-orm";
import { z } from "zod";
import { createInsertSchema } from "drizzle-zod";

// Tabla users
export const users = pgTable(
  "users",
  {
    id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
    username: text("username").notNull().unique(),
    passwordHash: text("password_hash").notNull(),
    email: text("email").notNull(),
    nombre: text("nombre"),
    telefono: text("telefono"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  },
  (table) => ({
    usernameIdx: uniqueIndex("users_username_idx").on(table.username),
  })
);

// Relaciones de usuarios
export const usersRelations = relations(users, ({ many }) => ({
  animals: many(animals),
  weightRecords: many(weightRecords),
  healthRecords: many(healthRecords),
  vaccinations: many(vaccinations),
  pestControl: many(pestControl),
  reproduction: many(reproduction),
  feeding: many(feeding),
  traceability: many(traceability),
  lotes: many(lotes),
  loteAnimals: many(loteAnimals), // Asegúrate de que esta relación exista si vas a usarla
}));

// Tabla animals
export const animals = pgTable(
  "animals",
  {
    id: serial("id").primaryKey(),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }), // userId ahora es UUID
    codigoUnico: text("codigo_unico").notNull().unique(),
    nombre: text("nombre"),
    raza: text("raza"),
    sexo: text("sexo").notNull(),
    fechaNacimiento: date("fecha_nacimiento"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  },
  (table) => ({
    codigoUnicoIdx: uniqueIndex("animals_codigo_unico_idx").on(table.codigoUnico),
    // El índice userIdIdx aquí no tiene sentido ser unique, a menos que un animal solo pueda existir para un único usuario, pero su objetivo principal es el código único del animal.
  })
);

// Relaciones de animales
export const animalsRelations = relations(animals, ({ one, many }) => ({
  user: one(users, { fields: [animals.userId], references: [users.id] }),
  weightRecords: many(weightRecords),
  healthRecords: many(healthRecords),
  vaccinations: many(vaccinations),
  pestControl: many(pestControl),
  reproduction: many(reproduction),
  feeding: many(feeding),
  traceability: many(traceability),
  loteAnimals: many(loteAnimals),
}));

// Tabla weight_records
export const weightRecords = pgTable(
  "weight_records",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    peso: integer("peso").notNull(),
    fecha: date("fecha").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí, ya que un animal puede tener múltiples registros de peso
);

// Relaciones de weight_records
export const weightRecordsRelations = relations(weightRecords, ({ one }) => ({
  animal: one(animals, { fields: [weightRecords.animalId], references: [animals.id] }),
  user: one(users, { fields: [weightRecords.userId], references: [users.id] }),
}));

export const healthRecords = pgTable(
  "health_records",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    fechaDiagnostico: date("fecha_diagnostico").notNull(),
    diagnostico: text("diagnostico").notNull(),
    tratamiento: text("tratamiento"),
    notasVeterinario: text("notas_veterinario"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const healthRecordsRelations = relations(healthRecords, ({ one }) => ({
  animal: one(animals, { fields: [healthRecords.animalId], references: [animals.id] }),
  user: one(users, { fields: [healthRecords.userId], references: [users.id] }),
}));

export const vaccinations = pgTable(
  "vaccinations",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    tipoVacuna: text("tipo_vacuna").notNull(),
    fechaAplicacion: date("fecha_aplicacion").notNull(),
    reaccionesAdversas: text("reacciones_adversas"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const vaccinationsRelations = relations(vaccinations, ({ one }) => ({
  animal: one(animals, { fields: [vaccinations.animalId], references: [animals.id] }),
  user: one(users, { fields: [vaccinations.userId], references: [users.id] }),
}));

export const pestControl = pgTable(
  "pest_control",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    tipoTratamiento: text("tipo_tratamiento").notNull(),
    fechaAplicacion: date("fecha_aplicacion").notNull(),
    resultados: text("resultados"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const pestControlRelations = relations(pestControl, ({ one }) => ({
  animal: one(animals, { fields: [pestControl.animalId], references: [animals.id] }),
  user: one(users, { fields: [pestControl.userId], references: [users.id] }),
}));

export const reproduction = pgTable(
  "reproduction",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    tipoEvento: text("tipo_evento").notNull(),
    fechaEvento: date("fecha_evento").notNull(),
    observaciones: text("observaciones"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const reproductionRelations = relations(reproduction, ({ one }) => ({
  animal: one(animals, { fields: [reproduction.animalId], references: [animals.id] }),
  user: one(users, { fields: [reproduction.userId], references: [users.id] }),
}));

export const feeding = pgTable(
  "feeding",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    tipoAlimento: text("tipo_alimento").notNull(),
    cantidad: integer("cantidad").notNull(),
    fecha: date("fecha").notNull(),
    observaciones: text("observaciones"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const feedingRelations = relations(feeding, ({ one }) => ({
  animal: one(animals, { fields: [feeding.animalId], references: [animals.id] }),
  user: one(users, { fields: [feeding.userId], references: [users.id] }),
}));

export const traceability = pgTable(
  "traceability",
  {
    id: serial("id").primaryKey(),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
    tipoEvento: text("tipo_evento").notNull(),
    fechaEvento: date("fecha_evento").notNull(), // Corregido, antes estaba cortado
    ubicacion: text("ubicacion").notNull(),
    detalles: text("detalles"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí
);

export const traceabilityRelations = relations(traceability, ({ one }) => ({
  animal: one(animals, { fields: [traceability.animalId], references: [animals.id] }),
  user: one(users, { fields: [traceability.userId], references: [users.id] }),
}));

export const lotes = pgTable(
  "lotes",
  {
    id: serial("id").primaryKey(),
    nombre: text("nombre").notNull(),
    descripcion: text("descripcion"),
    fincaId: integer("finca_id"), // Este campo parece no tener una referencia, asegúrate de que sea intencional
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }), // userId ahora es UUID
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
);

export const lotesRelations = relations(lotes, ({ one, many }) => ({
  user: one(users, { fields: [lotes.userId], references: [users.id] }),
  loteAnimals: many(loteAnimals),
}));

export const loteAnimals = pgTable(
  "lote_animals",
  {
    id: serial("id").primaryKey(),
    loteId: integer("lote_id").notNull().references(() => lotes.id, { onDelete: "cascade" }),
    animalId: integer("animal_id").notNull().references(() => animals.id, { onDelete: "cascade" }),
    fechaIngreso: timestamp("fecha_ingreso", { withTimezone: true }).defaultNow(),
    fechaSalida: timestamp("fecha_salida", { withTimezone: true }),
    userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }), // userId ahora es UUID
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
  }
  // No hay uniqueIndex aquí, ya que una combinación lote-animal puede tener múltiples registros de entrada/salida si el ID es serial
);

export const loteAnimalsRelations = relations(loteAnimals, ({ one }) => ({
  lote: one(lotes, { fields: [loteAnimals.loteId], references: [lotes.id] }),
  animal: one(animals, { fields: [loteAnimals.animalId], references: [animals.id] }),
  user: one(users, { fields: [loteAnimals.userId], references: [users.id] }),
}));

// Esquemas Zod para validación
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  email: true,
}).extend({
  password: z.string().min(6, "Contraseña debe tener al menos 6 caracteres"),
});

export const insertAnimalSchema = createInsertSchema(animals).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertWeightRecordSchema = createInsertSchema(weightRecords).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertHealthRecordSchema = createInsertSchema(healthRecords).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertVaccinationSchema = createInsertSchema(vaccinations).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertPestControlSchema = createInsertSchema(pestControl).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertReproductionSchema = createInsertSchema(reproduction).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertFeedingSchema = createInsertSchema(feeding).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertTraceabilitySchema = createInsertSchema(traceability).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertLoteSchema = createInsertSchema(lotes).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

export const insertLoteAnimalSchema = createInsertSchema(loteAnimals).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
});

// Tipos (CORREGIDO PARA USAR _type)
export type User = typeof users.$inferSelect;
export type InsertUser = typeof insertUserSchema._type; // CORREGIDO
export type SelectUser = User;

export type Animal = typeof animals.$inferSelect;
export type InsertAnimal = typeof insertAnimalSchema._type; // CORREGIDO

export type WeightRecord = typeof weightRecords.$inferSelect;
export type InsertWeightRecord = typeof insertWeightRecordSchema._type; // CORREGIDO

export type HealthRecord = typeof healthRecords.$inferSelect;
export type InsertHealthRecord = typeof insertHealthRecordSchema._type; // CORREGIDO

export type Vaccination = typeof vaccinations.$inferSelect;
export type InsertVaccination = typeof insertVaccinationSchema._type; // CORREGIDO

export type PestControl = typeof pestControl.$inferSelect;
export type InsertPestControl = typeof insertPestControlSchema._type; // CORREGIDO

export type Reproduction = typeof reproduction.$inferSelect;
export type InsertReproduction = typeof insertReproductionSchema._type; // CORREGIDO

export type Feeding = typeof feeding.$inferSelect;
export type InsertFeeding = typeof insertFeedingSchema._type; // CORREGIDO

export type Traceability = typeof traceability.$inferSelect;
export type InsertTraceability = typeof insertTraceabilitySchema._type; // CORREGIDO

export type Lote = typeof lotes.$inferSelect;
export type InsertLote = typeof insertLoteSchema._type; // CORREGIDO

export type LoteAnimal = typeof loteAnimals.$inferSelect;
export type InsertLoteAnimal = typeof insertLoteAnimalSchema._type; // CORREGIDO