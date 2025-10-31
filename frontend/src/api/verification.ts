import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

interface VerifyMentionResponse {
    success: boolean;
    message: string;
    mention_id: string;
    verified: boolean;
}

interface BulkVerifyRequest {
    stakeholder_id: string;
    case_id: string;
    filter_type: 'high' | 'medium' | 'all';
    verified: boolean;
}

interface BulkVerifyResponse {
    success: boolean;
    message: string;
    verified_count: number;
}

export const useVerifyMention = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ mentionId, verified }: { mentionId: string; verified: boolean }) => {
            const response = await apiClient.post<VerifyMentionResponse>(
                `/verification/mention/${mentionId}`,
                { verified }
            );
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
            queryClient.invalidateQueries({
                predicate: (query) =>
                    query.queryKey[0] === 'cases' &&
                    query.queryKey[1] !== undefined &&
                    query.queryKey[2] === 'stakeholders' &&
                    query.queryKey[3] === 'verification-status'
            });
        },
    });
};

export const useBulkVerifyMentions = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (request: BulkVerifyRequest) => {
            const response = await apiClient.post<BulkVerifyResponse>(
                '/verification/bulk',
                request
            );
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
            queryClient.invalidateQueries({
                queryKey: ['cases', variables.case_id, 'stakeholders', 'verification-status'],
            });
        },
    });
};

