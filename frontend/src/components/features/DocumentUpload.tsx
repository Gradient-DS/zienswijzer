import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useUploadDocument } from '@/api/documents';
import { Upload, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentUploadProps {
    caseId: string;
    onUploadComplete?: () => void;
}

export function DocumentUpload({ caseId, onUploadComplete }: DocumentUploadProps) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const uploadMutation = useUploadDocument();

    const handleFiles = (files: FileList | null) => {
        if (!files) return;

        const pdfFiles = Array.from(files).filter(file =>
            file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        );

        setSelectedFiles(prev => [...prev, ...pdfFiles]);
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

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        try {
            for (const file of selectedFiles) {
                await uploadMutation.mutateAsync({ caseId, file });
            }
            setSelectedFiles([]);
            onUploadComplete?.();
        } catch (error) {
            console.error('Upload failed:', error);
        }
    };

    return (
        <div className="space-y-4">
            <div
                className={cn(
                    'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
                    dragActive ? 'border-primary bg-primary/5' : 'border-border'
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-sm font-medium mb-2">
                    Sleep PDF bestanden hierheen of klik om te selecteren
                </p>
                <p className="text-xs text-muted-foreground mb-4">
                    Alleen PDF bestanden worden geaccepteerd
                </p>
                <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                >
                    Bestanden selecteren
                </Button>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    onChange={handleFileInput}
                    className="hidden"
                />
            </div>

            {selectedFiles.length > 0 && (
                <div className="space-y-2">
                    <h3 className="text-sm font-semibold">Geselecteerde bestanden:</h3>
                    <div className="space-y-2">
                        {selectedFiles.map((file, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-between p-3 bg-muted rounded-lg"
                            >
                                <span className="text-sm truncate flex-1">{file.name}</span>
                                <span className="text-xs text-muted-foreground mr-2">
                                    {(file.size / 1024).toFixed(1)} KB
                                </span>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => removeFile(index)}
                                    className="h-8 w-8 p-0"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                    </div>
                    <Button
                        onClick={handleUpload}
                        disabled={uploadMutation.isPending}
                        className="w-full"
                    >
                        {uploadMutation.isPending ? 'Uploaden...' : `${selectedFiles.length} bestand(en) uploaden`}
                    </Button>
                </div>
            )}

            {uploadMutation.isError && (
                <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                    Upload mislukt. Probeer het opnieuw.
                </div>
            )}
        </div>
    );
}

