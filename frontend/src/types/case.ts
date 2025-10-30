export interface Case {
    id: string;
    title: string;
    description: string;
    documentIds: string[];
    createdAt: string;
    updatedAt: string;
}

export interface CaseDetail extends Case {
    documents: Document[];
}

export interface Document {
    id: string;
    title: string;
    description?: string;
    type?: string;
    filePath?: string;
    fileSize?: number;
    pageCount?: number;
    processingStatus?: 'pending' | 'processing' | 'completed' | 'failed';
    uploadedAt?: string;
    processedAt?: string;
    createdAt: string;
    updatedAt: string;
    pdfUrl?: string;
}

