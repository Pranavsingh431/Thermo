import { useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardService } from '../services/dashboardService';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardService.getStats,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useRecentAnalyses = (limit = 10) => {
  return useQuery({
    queryKey: ['dashboard', 'recent-analyses', limit],
    queryFn: () => dashboardService.getRecentAnalyses(limit),
    staleTime: 30000,
    refetchInterval: 60000,
  });
};

export const useSubstations = () => {
  return useQuery({
    queryKey: ['dashboard', 'substations'],
    queryFn: dashboardService.getSubstations,
    staleTime: 300000, // 5 minutes (substations don't change often)
  });
};

export const useThermalScans = (params = {}) => {
  return useQuery({
    queryKey: ['dashboard', 'thermal-scans', params],
    queryFn: () => dashboardService.getThermalScans(params),
    staleTime: 30000,
  });
};

export const useAnalysisDetections = (analysisId) => {
  return useQuery({
    queryKey: ['dashboard', 'analysis', analysisId, 'detections'],
    queryFn: () => dashboardService.getAnalysisDetections(analysisId),
    enabled: !!analysisId,
    staleTime: 300000, // Detections are static once created
  });
};

// Hook to refresh all dashboard data
export const useDashboardRefresh = () => {
  const queryClient = useQueryClient();
  
  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };
  
  const refreshStats = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
  };
  
  const refreshAnalyses = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard', 'recent-analyses'] });
  };
  
  return {
    refreshAll,
    refreshStats,
    refreshAnalyses,
  };
}; 