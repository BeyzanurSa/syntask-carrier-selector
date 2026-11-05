import type { components } from "./schema";

type Schemas = components["schemas"];

export type StructuredOrder = Schemas["StructuredOrder"];
export type SelectionResponse = Schemas["SelectionResponse"];
export type SelectionSummary = Schemas["SelectionSummary"];
export type SelectionRecord = Schemas["SelectionRecord"];
export type SelectionStatus = SelectionResponse["status"];
export type ContainerSize = StructuredOrder["container_size"];
export type CargoType = StructuredOrder["cargo_type"];

export const CONTAINER_SIZES: ContainerSize[] = [20, 40, 45];
export const CARGO_TYPES: CargoType[] = ["Dry", "Reefer", "Hazardous"];
