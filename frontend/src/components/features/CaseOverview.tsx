import { useCaseOverview, type CaseOverview as CaseOverviewType } from '@/api/cases';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { CheckCircle2, XCircle, Clock, FileText, Users, Printer } from 'lucide-react';
import { useRef } from 'react';

interface CaseOverviewProps {
    caseId: string;
}

export function CaseOverview({ caseId }: CaseOverviewProps) {
    const { data: overview, isLoading, error } = useCaseOverview(caseId);
    const printRef = useRef<HTMLDivElement>(null);

    const handlePrint = () => {
        if (!printRef.current) return;
        const printWindow = window.open('', '_blank');
        if (!printWindow) return;

        const printContent = printRef.current.innerHTML;
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rapport - ${overview?.case_title || 'Zaak'}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        color: #333;
                    }
                    h1 { color: #1a1a1a; border-bottom: 2px solid #333; padding-bottom: 10px; }
                    h2 { color: #2a2a2a; margin-top: 30px; }
                    .document { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
                    .document.ok { background-color: #f0f9ff; border-color: #0ea5e9; }
                    .document.objected { background-color: #fef2f2; border-color: #ef4444; }
                    .chunk-objection { margin: 10px 0; padding: 10px; background-color: #fff; border-left: 3px solid #ef4444; }
                    .stakeholder-status { margin: 5px 0; padding: 8px; background-color: #f9fafb; }
                    .status-agree { color: #10b981; }
                    .status-disagree { color: #ef4444; }
                    .status-pending { color: #f59e0b; }
                    @media print {
                        body { padding: 20px; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                ${printContent}
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
        }, 250);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Overzicht laden...</div>
            </div>
        );
    }

    if (error || !overview) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-red-500">Fout bij laden van overzicht</div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6">
            <div ref={printRef} className="max-w-5xl mx-auto">
                <div className="flex justify-between items-center mb-6 no-print">
                    <h1 className="text-2xl font-bold">{overview.case_title}</h1>
                    <Button onClick={handlePrint} className="gap-2">
                        <Printer className="h-4 w-4" />
                        Rapport afdrukken
                    </Button>
                </div>

                <div className="print-only mb-6">
                    <h1 className="text-3xl font-bold mb-2">Rapport: {overview.case_title}</h1>
                    <p className="text-gray-600">Datum: {new Date().toLocaleDateString('nl-NL')}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 no-print">
                    <Card className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <FileText className="h-5 w-5 text-blue-600" />
                            <span className="font-semibold">Documenten</span>
                        </div>
                        <div className="text-2xl font-bold">{overview.total_documents}</div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <XCircle className="h-5 w-5 text-red-600" />
                            <span className="font-semibold">Bezwaar Chunks</span>
                        </div>
                        <div className="text-2xl font-bold">{overview.total_objected_chunks}</div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Users className="h-5 w-5 text-green-600" />
                            <span className="font-semibold">Reacties</span>
                        </div>
                        <div className="text-2xl font-bold">
                            {overview.stakeholders.filter(s => s.has_replied).length} / {overview.stakeholders.length}
                        </div>
                    </Card>
                </div>

                <section className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        Document Status
                    </h2>
                    <div className="space-y-4">
                        {overview.documents.map((doc) => (
                            <Card
                                key={doc.document_id}
                                className={`p-4 ${doc.is_ok ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {doc.is_ok ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                                        ) : (
                                            <XCircle className="h-5 w-5 text-red-600" />
                                        )}
                                        <h3 className="font-semibold text-lg">{doc.document_title}</h3>
                                    </div>
                                    <span className={`px-2 py-1 rounded text-sm font-medium ${doc.is_ok
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-red-100 text-red-800'
                                        }`}>
                                        {doc.is_ok ? 'OK' : `${doc.objected_chunks.length} bezwaren`}
                                    </span>
                                </div>
                                {doc.objected_chunks.length > 0 && (
                                    <div className="mt-3 space-y-2">
                                        <p className="font-medium text-sm text-gray-700">Bezwaar door:</p>
                                        {doc.objected_chunks.map((chunk, idx) => (
                                            <div key={idx} className="bg-white p-3 rounded border-l-4 border-red-500">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-sm font-medium text-red-700">
                                                        {chunk.stakeholder_name}
                                                    </span>
                                                    <span className="text-xs text-gray-500">- Pagina {chunk.page}</span>
                                                </div>
                                                <p className="text-sm text-gray-600 line-clamp-2">{chunk.context}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </Card>
                        ))}
                    </div>
                </section>

                <section className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Belanghebbenden Reacties
                    </h2>
                    <div className="space-y-2">
                        {overview.stakeholders.map((stakeholder) => (
                            <Card key={stakeholder.stakeholder_id} className="p-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        {stakeholder.has_replied ? (
                                            stakeholder.publication_status === 'agree' ? (
                                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                                            ) : stakeholder.publication_status === 'disagree' ? (
                                                <XCircle className="h-5 w-5 text-red-600" />
                                            ) : (
                                                <Clock className="h-5 w-5 text-yellow-600" />
                                            )
                                        ) : (
                                            <Clock className="h-5 w-5 text-gray-400" />
                                        )}
                                        <div>
                                            <p className="font-medium">{stakeholder.stakeholder_name}</p>
                                            <p className="text-sm text-gray-600">
                                                {stakeholder.has_replied
                                                    ? stakeholder.publication_status === 'agree'
                                                        ? 'Akkoord met publicatie'
                                                        : stakeholder.publication_status === 'disagree'
                                                            ? 'Bezwaar tegen publicatie'
                                                            : 'In behandeling'
                                                    : 'Nog geen reactie'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                </section>

                {overview.total_objected_chunks > 0 && (
                    <section className="mb-8">
                        <h2 className="text-xl font-semibold mb-4">Samenvatting</h2>
                        <Card className="p-4 bg-yellow-50 border-yellow-200">
                            <p className="text-sm text-gray-700">
                                Deze zaak heeft <strong>{overview.total_objected_chunks}</strong> chunk(s) waar bezwaar tegen is gemaakt.
                                Deze chunks moeten worden gecontroleerd voordat de documenten kunnen worden gepubliceerd.
                            </p>
                        </Card>
                    </section>
                )}
            </div>
        </div>
    );
}

