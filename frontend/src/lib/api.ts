/**
 * ProphetAI API client — calls Django REST backend, falls back to demo data.
 */

import { DEMO_PROPERTIES, getDemoProperty } from "./demo-data";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

// ──────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────

export interface RedFlag {
  issue?: string;
  category?: string;
  description?: string;
  severity: "Low" | "Medium" | "High" | "low" | "medium" | "high";
}

export interface PhotoInsight {
  photo_url: string;
  room_type: string;
  condition_score: number;
  observations: string[];
  renovation_needed: boolean;
  estimated_reno_cost_usd: number | null;
}

export interface ComparableSale {
  address: string;
  sale_price: number;
  bedrooms: number;
  square_feet: number;
  days_ago: number;
}

export interface ConfidenceInterval {
  low: number;
  high: number;
}

export type PropertyStatus = "pending" | "processing" | "completed" | "failed";

export interface PropertySummary {
  id: number;
  listing_url: string;
  address: string;
  city: string;
  state: string;
  bedrooms: number | null;
  bathrooms: number | null;
  square_feet: number | null;
  listing_price: number | null;
  ai_estimated_price: number | null;
  investment_score: number | null;
  status: PropertyStatus;
  red_flags: RedFlag[];
  photo_insights: PhotoInsight[];
  price_delta_pct: number | null;
  created_at: string;
}

export interface PropertyDetail extends PropertySummary {
  zip_code: string;
  lot_size_sqft: number | null;
  year_built: number | null;
  rental_yield_pct: number | null;
  appreciation_trend_pct: number | null;
  comparable_sales: ComparableSale[];
  photo_insights: PhotoInsight[];
  photos: { id: number; url: string; room_type: string; condition_score: number | null }[];
  analysed_at: string | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ──────────────────────────────────────────────
// API functions (with demo fallback)
// ──────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function getProperties(
  page = 1,
): Promise<PaginatedResponse<PropertySummary>> {
  try {
    return await request<PaginatedResponse<PropertySummary>>(
      `/properties/?page=${page}`,
    );
  } catch {
    // Backend unavailable — return demo data
    return {
      count: DEMO_PROPERTIES.length,
      next: null,
      previous: null,
      results: DEMO_PROPERTIES,
    };
  }
}

export async function getProperty(id: number): Promise<PropertyDetail> {
  try {
    return await request<PropertyDetail>(`/properties/${id}/`);
  } catch {
    return getDemoProperty(id);
  }
}

export async function analyseProperty(
  listingUrl: string,
): Promise<PropertyDetail> {
  try {
    return await request<PropertyDetail>("/analyse/", {
      method: "POST",
      body: JSON.stringify({ listing_url: listingUrl }),
    });
  } catch {
    // Demo mode — return first property
    return getDemoProperty(1);
  }
}
