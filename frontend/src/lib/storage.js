/**
 * LocalStorage utilities for managing shown alerts
 */

const STORAGE_KEY = "stockRotatorShownAlerts";

export const alertStorage = {
  get() {
    if (typeof window === "undefined") return {};
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  },

  set(alertsObj) {
    if (typeof window === "undefined") return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(alertsObj));
    } catch (error) {
      console.error("Failed to save to localStorage:", error);
    }
  },

  isShown(alertId) {
    const alerts = this.get();
    return !!alerts[alertId];
  },

  markAsShown(alertId) {
    const alerts = this.get();
    alerts[alertId] = true;
    this.set(alerts);
  },
};
