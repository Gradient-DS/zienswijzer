import { useState, useRef, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateCase, useUpdateCase, useCase } from '@/api/cases';
import { useUploadDocument } from '@/api/documents';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, X, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CreateCaseFormProps {
    caseId?: string;
}

export function CreateCaseForm({ caseId }: CreateCaseFormProps) {
    const isEditMode = !!caseId;
    const { data: caseData } = useCase(caseId);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();
    const createCase = useCreateCase();
    const updateCase = useUpdateCase();
    const uploadDocument = useUploadDocument();

    useEffect(() => {
        if (isEditMode && caseData) {
            setTitle(caseData.title);
            setDescription(caseData.description);
        }
    }, [isEditMode, caseData]);

    const handleFiles = (files: FileList | null) => {
        if (!files) return;

        const pdfFiles = Array.from(files).filter(file =>
            file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        );

        setSelectedFiles(prev => {
            const existingNames = new Set(prev.map(f => f.name));
            const newFiles = pdfFiles.filter(f => !existingNames.has(f.name));
            return [...prev, ...newFiles];
        });
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFiles(e.target.files);
    };

    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        try {
            let finalCaseId = caseId;

            if (isEditMode && caseId) {
                await updateCase.mutateAsync({
                    id: caseId,
                    title,
                    description,
                });
            } else {
                const response = await createCase.mutateAsync({
                    title,
                    description,
                });
                finalCaseId = response.data.case.id;
            }

            if (selectedFiles.length > 0 && finalCaseId) {
                for (const file of selectedFiles) {
                    await uploadDocument.mutateAsync({ caseId: finalCaseId, file });
                }
            }

            if (!isEditMode) {
                setTitle('');
                setDescription('');
            }
            setSelectedFiles([]);
            navigate(`/cases/${finalCaseId}?step=review`);
        } catch (error) {
            console.error(`Failed to ${isEditMode ? 'update' : 'create'} case:`, error);
        }
    };

    const isSubmitting = createCase.isPending || updateCase.isPending || uploadDocument.isPending;
    const existingDocuments = isEditMode ? caseData?.documents || [] : [];

    return (
        <div className="h-full flex flex-col bg-white">
            <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col p-6">
                <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
                    <div className="flex items-start justify-between mb-6">
                        <div className="space-y-1 flex-1 pr-4">
                            <h2 className="text-xl font-semibold text-gray-900">
                                {isEditMode ? 'Zaak bewerken' : 'Nieuwe zaak aanmaken'}
                            </h2>
                            <p className="text-sm text-gray-700">
                                {isEditMode
                                    ? 'Bewerk de zaakgegevens en upload eventueel extra PDF documenten'
                                    : 'Vul de gegevens in om een nieuwe zaak aan te maken.'}
                            </p>
                        </div>
                        <Button type="submit" disabled={isSubmitting} className="flex-shrink-0">
                            {isSubmitting
                                ? (createCase.isPending || updateCase.isPending
                                    ? `Zaak ${isEditMode ? 'bijwerken' : 'aanmaken'}...`
                                    : `${selectedFiles.length} bestand(en) uploaden...`)
                                : isEditMode ? 'Bijwerken' : 'Aanmaken'}
                        </Button>
                    </div>

                    <div className="flex-1 flex flex-col min-h-0 gap-6">
                        <div className="flex-shrink-0 space-y-6">
                            <div className="space-y-2">
                                <Label htmlFor="title">
                                    Titel <span className="text-destructive">*</span>
                                </Label>
                                <Input
                                    id="title"
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="Bijv. Rattenbestrijding Haarlem"
                                    required
                                    disabled={isSubmitting}
                                    aria-describedby={createCase.error ? 'title-error' : undefined}
                                    aria-invalid={createCase.error ? 'true' : 'false'}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">
                                    Beschrijving <span className="text-destructive">*</span>
                                </Label>
                                <Input
                                    id="description"
                                    type="text"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Bijv. Overzicht van de rattenbestrijding in Haarlem"
                                    required
                                    disabled={isSubmitting}
                                    aria-describedby={createCase.error ? 'description-error' : undefined}
                                    aria-invalid={createCase.error ? 'true' : 'false'}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label>PDF Documenten (optioneel)</Label>
                                <div
                                    className={cn(
                                        'border-2 border-dashed rounded-lg p-4 text-center transition-colors',
                                        dragActive ? 'border-primary bg-primary/5' : 'border-border'
                                    )}
                                    onDragEnter={handleDrag}
                                    onDragLeave={handleDrag}
                                    onDragOver={handleDrag}
                                    onDrop={handleDrop}
                                >
                                    <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                                    <p className="text-sm font-medium mb-1">
                                        Sleep PDF bestanden hierheen of klik om te selecteren
                                    </p>
                                    <p className="text-xs text-muted-foreground mb-3">
                                        Je kunt meerdere PDF's selecteren of een map met PDF's
                                    </p>
                                    <div className="flex gap-2 justify-center">
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => fileInputRef.current?.click()}
                                            disabled={isSubmitting}
                                            size="sm"
                                        >
                                            Bestanden selecteren
                                        </Button>
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => {
                                                const folderInput = document.createElement('input');
                                                folderInput.type = 'file';
                                                folderInput.webkitdirectory = true;
                                                folderInput.accept = '.pdf,application/pdf';
                                                folderInput.multiple = true;
                                                folderInput.onchange = (e) => {
                                                    const target = e.target as HTMLInputElement;
                                                    handleFiles(target.files);
                                                };
                                                folderInput.click();
                                            }}
                                            disabled={isSubmitting}
                                            size="sm"
                                        >
                                            Map selecteren
                                        </Button>
                                    </div>
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".pdf,application/pdf"
                                        multiple
                                        onChange={handleFileInput}
                                        className="hidden"
                                        disabled={isSubmitting}
                                    />
                                </div>
                            </div>
                        </div>

                        {(selectedFiles.length > 0 || (isEditMode && existingDocuments.length > 0)) && (
                            <div className="flex flex-col mb-6">
                                <Label className="flex-shrink-0 mb-2">
                                    {selectedFiles.length > 0 && isEditMode && existingDocuments.length > 0
                                        ? `Toegevoegde documenten (${selectedFiles.length + existingDocuments.length})`
                                        : selectedFiles.length > 0
                                            ? `Geselecteerde bestanden (${selectedFiles.length})`
                                            : `Toegevoegde documenten (${existingDocuments.length})`}
                                </Label>
                                <div className="h-[30vh] max-h-80 overflow-y-auto border rounded-lg p-3 bg-muted/50">
                                    <div className="space-y-2">
                                        {selectedFiles.map((file, index) => (
                                            <div
                                                key={`selected-${index}`}
                                                className="flex items-center justify-between p-2 bg-background rounded-md"
                                            >
                                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                                    <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                                    <div className="flex-1 min-w-0">
                                                        <div className="text-sm font-medium truncate">
                                                            {file.name}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground">
                                                            {(file.size / 1024).toFixed(1)} KB
                                                        </div>
                                                    </div>
                                                </div>
                                                <Button
                                                    type="button"
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => removeFile(index)}
                                                    disabled={isSubmitting}
                                                    className="h-7 w-7 p-0"
                                                >
                                                    <X className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        ))}
                                        {isEditMode && existingDocuments.map((document) => (
                                            <div
                                                key={document.id}
                                                className="flex items-center gap-2 p-2 bg-background rounded-md"
                                            >
                                                <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-sm font-medium truncate">
                                                        {document.title}
                                                    </div>
                                                    <div className="flex items-center gap-2 mt-0.5">
                                                        {document.page_count && (
                                                            <span className="text-xs text-muted-foreground">
                                                                {document.page_count} pagina{document.page_count !== 1 ? "'s" : ''}
                                                            </span>
                                                        )}
                                                        {document.parse_status && (
                                                            <span className={cn(
                                                                'px-1.5 py-0.5 rounded text-xs font-medium',
                                                                document.parse_status === 'completed' && 'bg-green-100 text-green-800',
                                                                document.parse_status === 'processing' && 'bg-yellow-100 text-yellow-800',
                                                                document.parse_status === 'pending' && 'bg-gray-100 text-gray-800',
                                                                document.parse_status === 'failed' && 'bg-red-100 text-red-800'
                                                            )}>
                                                                {document.parse_status}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>

                    {(createCase.error || updateCase.error || uploadDocument.isError) && (
                        <div
                            id="error-message"
                            role="alert"
                            className="p-4 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm mt-6"
                        >
                            {createCase.error || updateCase.error
                                ? `Het ${isEditMode ? 'bijwerken' : 'aanmaken'} van de zaak is mislukt. Probeer het opnieuw.`
                                : 'Het uploaden van documenten is mislukt. De zaak is bijgewerkt, maar probeer de documenten opnieuw te uploaden.'}
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
}

