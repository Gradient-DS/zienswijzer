import { useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useStakeholderMentions } from '@/api/stakeholders';
import { useCase } from '@/api/cases';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Stakeholder, ChunkDetail, StakeholderMention } from '@/types';

interface StakeholderDetailViewProps {
    caseId: string;
    stakeholderId: string;
    stakeholder: Stakeholder;
}

const STAKEHOLDER_COLORS: Record<string, string> = {
    organization: '#3B82F6',
    individual: '#10B981',
    government: '#F59E0B',
    community: '#8B5CF6',
    environmental: '#059669',
    default: '#6B7280',
};

function getStakeholderColor(type: string): string {
    return STAKEHOLDER_COLORS[type] || STAKEHOLDER_COLORS.default;
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
    const percentage = Math.round(confidence * 100);
    const colorClass =
        confidence >= 0.9
            ? 'bg-green-500'
            : confidence >= 0.7
                ? 'bg-yellow-500'
                : 'bg-red-500';

    return (
        <span
            className={cn(
                'px-2 py-0.5 rounded text-xs font-semibold text-white',
                colorClass
            )}
        >
            {percentage}%
        </span>
    );
}

function ChunkCard({
    chunk,
    mention,
    documentTitle,
    onNavigateToDocument,
}: {
    chunk: ChunkDetail;
    mention: StakeholderMention;
    documentTitle: string;
    onNavigateToDocument: (documentId: string, page: number) => void;
}) {
    const color = getStakeholderColor(mention.stakeholder.type);

    return (
        <Card
            className="cursor-pointer hover:shadow-md transition-all border-2"
            onClick={() => onNavigateToDocument(chunk.document_id, chunk.page)}
        >
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <div
                                className="w-3 h-3 rounded-full flex-shrink-0"
                                style={{ backgroundColor: color }}
                            />
                            <h4 className="font-semibold text-sm text-gray-900 truncate">
                                {documentTitle}
                            </h4>
                        </div>
                        <p className="text-xs text-gray-500">
                            Pagina {chunk.page}
                        </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {mention.verified ? (
                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                            <XCircle className="h-4 w-4 text-gray-400" />
                        )}
                        <ConfidenceBadge confidence={mention.confidence} />
                    </div>
                </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
                <div>
                    <p className="text-xs font-medium text-gray-600 mb-1">
                        Vermelding:
                    </p>
                    <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded border border-gray-200 italic">
                        "{mention.mention_text}"
                    </p>
                </div>
                <div>
                    <p className="text-xs font-medium text-gray-600 mb-1">
                        Context:
                    </p>
                    <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded border border-gray-200 line-clamp-3">
                        {chunk.context}
                    </p>
                </div>
            </CardContent>
        </Card>
    );
}

export function StakeholderDetailView({
    caseId,
    stakeholderId,
    stakeholder,
}: StakeholderDetailViewProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { data: chunks, isLoading } = useStakeholderMentions(caseId, stakeholderId);
    const { data: caseData } = useCase(caseId);

    const documentMap = useMemo(() => {
        if (!caseData?.documents) return new Map();
        return new Map(caseData.documents.map(doc => [doc.id, doc]));
    }, [caseData]);

    const { unverifiedChunks, verifiedChunks } = useMemo(() => {
        if (!chunks) {
            return {
                unverifiedChunks: [],
                verifiedChunks: [],
            };
        }

        const unverified: Array<{ chunk: ChunkDetail; mention: StakeholderMention }> = [];
        const verified: Array<{ chunk: ChunkDetail; mention: StakeholderMention }> = [];

        chunks.forEach(chunk => {
            chunk.stakeholder_mentions.forEach(mention => {
                if (!mention.verified) {
                    unverified.push({ chunk, mention });
                } else {
                    verified.push({ chunk, mention });
                }
            });
        });

        return { unverifiedChunks: unverified, verifiedChunks: verified };
    }, [chunks]);

    const handleNavigateToDocument = (documentId: string, page: number) => {
        const newSearchParams = new URLSearchParams(location.search);
        newSearchParams.set('document', documentId);
        newSearchParams.set('step', 'review');
        newSearchParams.delete('stakeholder');
        navigate(`${location.pathname}?${newSearchParams.toString()}`);
    };

    const color = getStakeholderColor(stakeholder.type);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Laden...</div>
            </div>
        );
    }

    if (!chunks || chunks.length === 0) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <p className="text-lg font-medium mb-2">Geen vermeldingen gevonden</p>
                    <p className="text-sm text-gray-500">
                        Deze belanghebbende komt niet voor in de documenten
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            <div className="space-y-2">
                <div className="flex items-center gap-3">
                    <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: color }}
                    />
                    <h1 className="text-2xl font-semibold text-gray-900">
                        {stakeholder.name}
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 capitalize">
                        {stakeholder.type}
                    </span>
                    {stakeholder.contact_info && (
                        <span className="text-sm text-gray-600">
                            {stakeholder.contact_info}
                        </span>
                    )}
                </div>
            </div>

            {unverifiedChunks.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Te verifiëren ({unverifiedChunks.length})
                        </h2>
                    </div>
                    <div className="space-y-3">
                        {unverifiedChunks.map(({ chunk, mention }) => {
                            const document = documentMap.get(chunk.document_id);
                            return (
                                <ChunkCard
                                    key={`${chunk.id}-${mention.id}`}
                                    chunk={chunk}
                                    mention={mention}
                                    documentTitle={document?.title || 'Onbekend document'}
                                    onNavigateToDocument={handleNavigateToDocument}
                                />
                            );
                        })}
                    </div>
                </div>
            )}

            {verifiedChunks.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <h2 className="text-lg font-semibold text-gray-900">
                            Geverifieerd ({verifiedChunks.length})
                        </h2>
                    </div>
                    <div className="space-y-3">
                        {verifiedChunks.map(({ chunk, mention }) => {
                            const document = documentMap.get(chunk.document_id);
                            return (
                                <ChunkCard
                                    key={`${chunk.id}-${mention.id}`}
                                    chunk={chunk}
                                    mention={mention}
                                    documentTitle={document?.title || 'Onbekend document'}
                                    onNavigateToDocument={handleNavigateToDocument}
                                />
                            );
                        })}
                    </div>
                </div>
            )}

            {unverifiedChunks.length === 0 && verifiedChunks.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                    <p>Geen vermeldingen gevonden voor deze belanghebbende</p>
                </div>
            )}
        </div>
    );
}

