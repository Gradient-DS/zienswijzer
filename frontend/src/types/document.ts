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
    contact_info: string;
    publication_status?: 'agree' | 'disagree' | 'pending' | null;
    created_at: string;
    updated_at: string;
}

export interface StakeholderMention {
    id: string;
    chunk_id: string;
    stakeholder_id: string;
    stakeholder: Stakeholder;
    confidence: number;
    mention_text: string;
    mention_bbox: BoundingBox;
    checked: boolean;
    accepted: boolean | null;
    rejected: boolean | null;
    created_at: string;
}

export interface ChunkDetail {
    id: string;
    document_id: string;
    page: number;
    context: string;
    bbox: BoundingBox;
    stakeholder_mentions: StakeholderMention[];
}

