/**
 * BioFusion AI — API Client
 * Centralized fetch wrapper for backend communication.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`BioFusion API error [${endpoint}]:`, error);
    throw error;
  }
}

export const api = {
  search: (query, type = null) => {
    const params = new URLSearchParams({ q: query });
    if (type) params.append("type", type);
    return request(`/search?${params}`);
  },

  getGene: (id, include = null) => {
    const params = include ? `?include=${include}` : "";
    return request(`/gene/${id}${params}`);
  },

  getVariant: (id) => request(`/variant/${id}`),

  getDrug: (id) => request(`/drug/${id}`),

  getDisease: (id) => request(`/disease/${id}`),

  getNetwork: (gene, limit = 20) =>
    request(`/network/${gene}?limit=${limit}`),

  getHealth: () => request("/health"),
};

export default api;
