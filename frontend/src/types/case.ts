import type { ChunkDetail } from './document';

export interface Case {
    id: string;
    title: string;
    description: string;
    document_ids: string[];
    created_at: string;
    updated_at: string;
}

export interface CaseDetail extends Case {
    documents: Document[];
}

export interface Document {
    id: string;
    title: string;
    description?: string;
    type?: string;
    keywords?: string;
    author?: string;
    file_path?: string;
    file_size?: number;
    page_count?: number;
    parse_status?: string;
    uploaded_at?: string;
    processed_at?: string;
    created_at: string;
    updated_at: string;
    pdf_url?: string;
    chunks?: ChunkDetail[];
}
