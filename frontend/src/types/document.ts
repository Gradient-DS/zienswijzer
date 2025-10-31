export interface BoundingBox {
    x: number;
    y: number;
    width: number;
    height: number;
}

export interface Stakeholder {
    id: string;
    type: string;
    name: string;
    contactInfo: string;
    createdAt: string;
    updatedAt: string;
}

export interface StakeholderMention {
    id: string;
    chunkId: string;
    stakeholderId: string;
    stakeholder: Stakeholder;
    confidence: number;
    mentionText: string;
    mentionBbox: BoundingBox;
    verified: boolean;
    createdAt: string;
}

export interface ChunkDetail {
    id: string;
    documentId: string;
    page: number;
    context: string;
    bbox: BoundingBox;
    stakeholderMentions: StakeholderMention[];
}

