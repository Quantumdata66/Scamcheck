/**
 * ScamCheck API Service
 * Handles communication with the FastAPI backend.
 */

// Resolves API Base URL:
// 1. Explicit VITE_API_BASE_URL if configured in environment
// 2. http://localhost:8000 in local Vite development mode (import.meta.env.DEV)
// 3. '' (same-origin relative paths) in production builds / Vercel unified deployment
const rawBaseUrl =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL
    : import.meta.env.DEV
      ? 'http://localhost:8000'
      : '';

const API_BASE_URL = rawBaseUrl.replace(/\/+$/, '');

/**
 * Sends a suspicious text message to the backend for analysis.
 *
 * @param {string} text - The text content to analyze.
 * @returns {Promise<Object>} The structured CheckResponse.
 */
export async function checkMessage(text) {
  try {
    const url = `${API_BASE_URL}/check`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      let errorMessage = `Server error (${response.status})`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((err) => err.msg || err.message).join('; ');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          }
        }
      } catch {
        // Response was not JSON
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('Unable to connect to the ScamCheck analysis server. Please check your connection or ensure the backend is running.');
    }
    throw error;
  }
}

/**
 * Checks the operational health of the backend API.
 *
 * @returns {Promise<Object>} The health response object.
 */
export async function checkHealth() {
  const url = `${API_BASE_URL}/health`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return await response.json();
}
