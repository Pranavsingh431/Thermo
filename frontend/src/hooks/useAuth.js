import { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/authService';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Login function
  const login = useCallback(async (username, password) => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await authService.login(username, password);
      const userData = await authService.getCurrentUser();
      
      setUser(userData);
      return { success: true, data };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // Logout function
  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setError(null);
  }, []);

  // Verify token and get user info
  const verifyToken = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!authService.isAuthenticated()) {
        setUser(null);
        return;
      }

      const userData = await authService.verifyToken();
      setUser(userData);
    } catch (err) {
      console.error('Token verification failed:', err);
      authService.logout();
      setUser(null);
      setError('Session expired');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize auth state on mount
  useEffect(() => {
    verifyToken();
  }, [verifyToken]);

  return {
    user,
    loading,
    error,
    login,
    logout,
    verifyToken,
    isAuthenticated: !!user,
  };
}; 