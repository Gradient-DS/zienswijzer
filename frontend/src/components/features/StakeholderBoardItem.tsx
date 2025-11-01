import { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { getStakeholderStatus } from '@/lib/stakeholder-status';
import type { StakeholderStatus } from '@/lib/stakeholder-status';
import type { Stakeholder, ChunkDetail } from '@/types';
import type { SentEmail } from '@/types/email';
import { cn } from '@/lib/utils';
import { STATUS_COLUMNS } from './StakeholderBoard';
import { CheckCircle, AlertCircle } from 'lucide-react';

interface StakeholderBoardItemProps {
    stakeholder: Stakeholder;
    targetStatus: StakeholderStatus;
    onClick: () => void;
    chunks: ChunkDetail[];
    sentEmails: SentEmail[];
}

export function StakeholderBoardItem({
    stakeholder,
    targetStatus,
    onClick,
    chunks,
    sentEmails,
}: StakeholderBoardItemProps) {
    const status = useMemo(() => {
        if (!chunks || chunks.length === 0) {
            return 'not_processed' as StakeholderStatus;
        }
        return getStakeholderStatus({
            chunks,
            sentEmails,
            stakeholderId: stakeholder.id,
            contactInfo: stakeholder.contact_info,
        });
    }, [chunks, sentEmails, stakeholder.id, stakeholder.contact_info]);

    const shouldRender = status === targetStatus;

    // Only render if this stakeholder's status matches the column
    if (!shouldRender) {
        return null;
    }

    const statusColumn = STATUS_COLUMNS.find(col => col.id === status);

    const getPublicationStatusIcon = () => {
        if (status !== 'responded') return null;

        if (stakeholder.publication_status === 'agree') {
            return (
                <div title="Akkoord met publicatie">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                </div>
            );
        }

        if (stakeholder.publication_status === 'disagree') {
            return (
                <div title="Bezwaar tegen publicatie">
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                </div>
            );
        }

        return null;
    };

    return (
        <Card
            className={cn(
                'mb-3 cursor-pointer hover:shadow-md transition-all border-2',
                'hover:border-primary'
            )}
            onClick={onClick}
        >
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm text-gray-900 truncate">
                            {stakeholder.name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500 capitalize">
                                {stakeholder.type}
                            </span>
                            {stakeholder.contact_info && (
                                <>
                                    <span className="text-xs text-gray-400">•</span>
                                    <span className="text-xs text-gray-500 truncate">
                                        {stakeholder.contact_info}
                                    </span>
                                </>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {getPublicationStatusIcon()}
                        {statusColumn && (
                            <div className={cn(statusColumn.color)}>
                                {statusColumn.icon}
                            </div>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

