import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Stakeholder, ChunkDetail } from '@/types';

interface StakeholderListResponse {
    stakeholders: Stakeholder[];
}

interface ChunkListResponse {
    chunks: ChunkDetail[];
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

export const useStakeholderMentions = (caseId: string | undefined, stakeholderId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'stakeholders', stakeholderId, 'mentions'],
        queryFn: async () => {
            if (!caseId || !stakeholderId) return [];

            try {
                const caseRes = await apiClient.get(`/cases/${caseId}`);
                const documents = caseRes.data.case.documents || [];

                const allChunks: ChunkDetail[] = [];

                for (const doc of documents) {
                    try {
                        const chunksRes = await apiClient.get<ChunkListResponse>(`/documents/${doc.id}/chunks`);
                        const chunks = chunksRes.data.chunks || [];

                        const filteredChunks = chunks
                            .map(chunk => ({
                                ...chunk,
                                stakeholder_mentions: chunk.stakeholder_mentions.filter(
                                    mention => mention.stakeholder_id === stakeholderId
                                )
                            }))
                            .filter(chunk => chunk.stakeholder_mentions.length > 0);

                        allChunks.push(...filteredChunks);
                    } catch (error) {
                        console.error(`Failed to fetch chunks for document ${doc.id}:`, error);
                    }
                }

                return allChunks;
            } catch (error) {
                console.error('Failed to fetch stakeholder mentions:', error);
                return [];
            }
        },
        enabled: !!caseId && !!stakeholderId,
    });
};

