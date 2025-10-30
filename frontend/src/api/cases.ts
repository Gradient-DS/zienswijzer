import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Case, CaseDetail } from '@/types';

interface CaseListResponse {
    cases: Case[];
}

interface CaseDetailResponse {
    case: CaseDetail;
}

interface CreateCaseRequest {
    title: string;
    description: string;
    password?: string;
}

interface CreateCaseResponse {
    case: Case;
}

export const useCases = () => {
    return useQuery({
        queryKey: ['cases'],
        queryFn: async () => {
            const res = await apiClient.get<CaseListResponse>('/cases');
            return res.data.cases;
        },
    });
};

export const useCase = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId],
        queryFn: async () => {
            const res = await apiClient.get<CaseDetailResponse>(`/cases/${caseId}`);
            return res.data.case;
        },
        enabled: !!caseId,
    });
};

export const useCreateCase = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: CreateCaseRequest) =>
            apiClient.post<CreateCaseResponse>('/cases', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
        },
    });
};

