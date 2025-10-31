import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Stakeholder } from '@/types';

interface StakeholderListResponse {
    stakeholders: Stakeholder[];
}

export const useCaseStakeholders = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'stakeholders'],
        queryFn: async () => {
            try {
                const res = await apiClient.get<StakeholderListResponse>(`/cases/${caseId}/stakeholders`);
                return res.data.stakeholders;
            } catch (error) {
                return [];
            }
        },
        enabled: !!caseId,
    });
};

