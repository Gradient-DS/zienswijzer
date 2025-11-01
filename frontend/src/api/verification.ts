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

interface BulkAcceptRequest {
    mentionIds: string[];
    caseId: string;
}

export const useBulkAcceptMentions = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ mentionIds, caseId }: BulkAcceptRequest) => {
            await Promise.all(
                mentionIds.map((mentionId) =>
                    apiClient.post<VerifyMentionResponse>(
                        `/verification/mention/${mentionId}`,
                        { verified: true, case_id: caseId }
                    )
                )
            );
            return { success: true, count: mentionIds.length };
        },
        onMutate: async ({ mentionIds, caseId }) => {
            // Cancel outgoing refetches
            await queryClient.cancelQueries({ queryKey: ['documents'] });
            await queryClient.cancelQueries({ queryKey: ['cases'] });

            // Snapshot previous values
            const previousDocuments = new Map();
            const previousCases = new Map();

            // Get all document queries and update them optimistically
            queryClient.getQueriesData({ queryKey: ['documents'] }).forEach(([key, data]) => {
                if (data && typeof data === 'object' && 'document' in data) {
                    previousDocuments.set(key, data);

                    const updatedData = JSON.parse(JSON.stringify(data));
                    if (updatedData.document?.chunks) {
                        updatedData.document.chunks = updatedData.document.chunks.map((chunk: any) => ({
                            ...chunk,
                            stakeholder_mentions: chunk.stakeholder_mentions.map((mention: any) => {
                                if (mentionIds.includes(mention.id)) {
                                    return {
                                        ...mention,
                                        checked: true,
                                        accepted: true,
                                        rejected: null,
                                    };
                                }
                                return mention;
                            }),
                        }));
                    }
                    queryClient.setQueryData(key, updatedData);
                }
            });

            // Update case queries optimistically
            queryClient.getQueriesData({ queryKey: ['cases', caseId] }).forEach(([key, data]) => {
                if (data && typeof data === 'object' && 'chunks' in data) {
                    previousCases.set(key, data);

                    const updatedData = JSON.parse(JSON.stringify(data));
                    if (updatedData.chunks) {
                        updatedData.chunks = updatedData.chunks.map((chunk: any) => ({
                            ...chunk,
                            stakeholder_mentions: chunk.stakeholder_mentions.map((mention: any) => {
                                if (mentionIds.includes(mention.id)) {
                                    return {
                                        ...mention,
                                        checked: true,
                                        accepted: true,
                                        rejected: null,
                                    };
                                }
                                return mention;
                            }),
                        }));
                    }
                    queryClient.setQueryData(key, updatedData);
                }
            });

            return { previousDocuments, previousCases };
        },
        onError: (_err, _variables, context) => {
            // Revert optimistic updates on error
            if (context?.previousDocuments) {
                context.previousDocuments.forEach((data, key) => {
                    queryClient.setQueryData(key, data);
                });
            }
            if (context?.previousCases) {
                context.previousCases.forEach((data, key) => {
                    queryClient.setQueryData(key, data);
                });
            }
        },
        onSuccess: (_, variables) => {
            // Refetch to ensure consistency with server
            queryClient.invalidateQueries({ queryKey: ['cases'] });
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
            if (variables.caseId) {
                queryClient.invalidateQueries({ queryKey: ['cases', variables.caseId, 'document-completion'] });
            }
        },
    });
};

