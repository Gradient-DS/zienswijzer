import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Stakeholder, ChunkDetail } from '@/types';
import { transformChunkDetail } from '@/lib/mention-utils';

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
                        const chunksRes = await apiClient.get<any>(`/documents/${doc.id}/chunks`, {
                            params: { case_id: caseId }
                        });
                        const chunks = (chunksRes.data.chunks || []).map(transformChunkDetail);

                        const filteredChunks = chunks
                            .map((chunk: ChunkDetail) => ({
                                ...chunk,
                                stakeholder_mentions: chunk.stakeholder_mentions.filter(
                                    (mention: any) => mention.stakeholder_id === stakeholderId
                                )
                            }))
                            .filter((chunk: ChunkDetail) => chunk.stakeholder_mentions.length > 0);

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

export const useStakeholderVerificationStatus = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'stakeholders', 'verification-status'],
        queryFn: async () => {
            if (!caseId) return new Set<string>();

            try {
                const caseRes = await apiClient.get(`/cases/${caseId}`);
                const documents = caseRes.data.case.documents || [];

                const stakeholderMentions = new Map<string, { verified: number; total: number }>();

                for (const doc of documents) {
                    try {
                        const chunksRes = await apiClient.get<any>(`/documents/${doc.id}/chunks`, {
                            params: { case_id: caseId }
                        });
                        const chunks = (chunksRes.data.chunks || []).map(transformChunkDetail);

                        chunks.forEach((chunk: ChunkDetail) => {
                            chunk.stakeholder_mentions.forEach((mention: any) => {
                                const current = stakeholderMentions.get(mention.stakeholder_id) || { verified: 0, total: 0 };
                                current.total += 1;
                                if (mention.checked && mention.accepted) {
                                    current.verified += 1;
                                }
                                stakeholderMentions.set(mention.stakeholder_id, current);
                            });
                        });
                    } catch (error) {
                        console.error(`Failed to fetch chunks for document ${doc.id}:`, error);
                    }
                }

                const verifiedStakeholderIds = new Set<string>();
                stakeholderMentions.forEach((counts, stakeholderId) => {
                    if (counts.total > 0 && counts.verified === counts.total) {
                        verifiedStakeholderIds.add(stakeholderId);
                    }
                });

                return verifiedStakeholderIds;
            } catch (error) {
                console.error('Failed to fetch stakeholder verification status:', error);
                return new Set<string>();
            }
        },
        enabled: !!caseId,
    });
};

export const useAllStakeholderMentions = (caseId: string | undefined) => {
    return useQuery({
        queryKey: ['cases', caseId, 'all-stakeholder-mentions'],
        queryFn: async () => {
            if (!caseId) return new Map<string, ChunkDetail[]>();

            try {
                const caseRes = await apiClient.get(`/cases/${caseId}`);
                const documents = caseRes.data.case.documents || [];

                const stakeholderChunksMap = new Map<string, ChunkDetail[]>();

                for (const doc of documents) {
                    try {
                        const chunksRes = await apiClient.get<any>(`/documents/${doc.id}/chunks`, {
                            params: { case_id: caseId }
                        });
                        const chunks = (chunksRes.data.chunks || []).map(transformChunkDetail);

                        chunks.forEach((chunk: ChunkDetail) => {
                            chunk.stakeholder_mentions.forEach((mention: any) => {
                                const stakeholderId = mention.stakeholder_id;
                                if (!stakeholderChunksMap.has(stakeholderId)) {
                                    stakeholderChunksMap.set(stakeholderId, []);
                                }

                                const existingChunks = stakeholderChunksMap.get(stakeholderId)!;
                                const chunkIndex = existingChunks.findIndex(c => c.id === chunk.id);

                                if (chunkIndex === -1) {
                                    const filteredChunk = {
                                        ...chunk,
                                        stakeholder_mentions: chunk.stakeholder_mentions.filter(
                                            (m: any) => m.stakeholder_id === stakeholderId
                                        )
                                    };
                                    existingChunks.push(filteredChunk);
                                }
                            });
                        });
                    } catch (error) {
                        console.error(`Failed to fetch chunks for document ${doc.id}:`, error);
                    }
                }

                return stakeholderChunksMap;
            } catch (error) {
                console.error('Failed to fetch all stakeholder mentions:', error);
                return new Map<string, ChunkDetail[]>();
            }
        },
        enabled: !!caseId,
        staleTime: 5 * 60 * 1000,
    });
};

