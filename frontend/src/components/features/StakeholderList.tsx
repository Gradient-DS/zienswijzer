import type { Stakeholder } from '@/types';
import { Users } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StakeholderListProps {
    stakeholders: Stakeholder[];
    selectedStakeholderId?: string;
    onSelectStakeholder?: (stakeholderId: string) => void;
}

export function StakeholderList({
    stakeholders,
    selectedStakeholderId,
    onSelectStakeholder,
}: StakeholderListProps) {
    if (stakeholders.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                <p>Geen belanghebbenden beschikbaar</p>
            </div>
        );
    }

    const uniqueStakeholders = Array.from(
        new Map(stakeholders.map(s => [s.id, s])).values()
    );

    return (
        <div className="space-y-1">
            {uniqueStakeholders.map((stakeholder) => (
                <div
                    key={stakeholder.id}
                    className={cn(
                        'flex items-start gap-2 px-2 py-2 rounded-md cursor-pointer transition-colors',
                        selectedStakeholderId === stakeholder.id
                            ? 'bg-gray-200 text-gray-900'
                            : 'hover:bg-gray-100 text-gray-700'
                    )}
                    onClick={() => onSelectStakeholder?.(stakeholder.id)}
                >
                    <Users className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">
                            {stakeholder.name}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-muted-foreground">
                                {stakeholder.type}
                            </span>
                            {stakeholder.contact_info && (
                                <span className="text-xs text-muted-foreground truncate">
                                    {stakeholder.contact_info}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

