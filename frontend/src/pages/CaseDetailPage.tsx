import { useParams } from 'react-router-dom';
import { useCase } from '@/api/cases';

export default function CaseDetailPage() {
    const { id } = useParams<{ id: string }>();
    const { data: caseData, isLoading, error } = useCase(id);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Zaak laden...</div>
            </div>
        );
    }

    if (error || !caseData) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-red-500">Zaak niet gevonden</div>
            </div>
        );
    }

    return (
        <div className="p-8">
            <div className="space-y-4">
                <h1 className="text-3xl font-bold text-gray-900">{caseData.title}</h1>
                <div className="text-sm text-gray-500">Zaak ID: {caseData.id}</div>
                <p className="text-gray-700">{caseData.description}</p>
            </div>
        </div>
    );
}

