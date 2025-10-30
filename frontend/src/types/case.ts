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
    content?: string;
    createdAt: string;
    updatedAt: string;
    authorId: string;
}

