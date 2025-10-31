import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import { transformVerifiedToBackend } from '@/lib/mention-utils';

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
        mutationFn: async ({
            mentionId,
            checked,
            accepted,
            rejected,
            caseId
        }: {
            mentionId: string;
            checked: boolean;
            accepted: boolean | null;
            rejected: boolean | null;
            caseId: string
        }) => {
            const verified = transformVerifiedToBackend(checked, accepted, rejected);
            const response = await apiClient.post<VerifyMentionResponse>(
                `/verification/mention/${mentionId}`,
                { verified, case_id: caseId }
            );
            return response.data;
        },
        onSuccess: (_, variables) => {
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
            if (variables.caseId) {
                queryClient.invalidateQueries({ queryKey: ['cases', variables.caseId, 'document-completion'] });
            }
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
            queryClient.invalidateQueries({ queryKey: ['cases', variables.case_id, 'document-completion'] });
        },
    });
};

interface RemoveMentionResponse {
    success: boolean;
    message: string;
    mention_id: string;
}

export const useRemoveMention = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (mentionId: string) => {
            const response = await apiClient.delete<RemoveMentionResponse>(
                `/verification/mention/${mentionId}`
            );
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cases'] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
        },
    });
};

