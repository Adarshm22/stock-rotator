/**
 * API configuration and utilities
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  async fetchRow() {
    const response = await fetch(`${API_URL}/row`);
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  },

  async sendMessage(message, commandTime) {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, command_time: commandTime }),
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  },

  async fetchConditions() {
    const response = await fetch(`${API_URL}/conditions`);
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  },
};
