import { useRef, useState } from "react";
import "./ImageUploader.css";
import "./MultiImageUploader.css";

interface MultiImageUploaderProps {
  onFilesSelected: (files: File[]) => void;
  label: string;
  disabled?: boolean;
}

export function MultiImageUploader({ onFilesSelected, label, disabled }: MultiImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previews, setPreviews] = useState<{ url: string; name: string }[]>([]);
  const [dragOver, setDragOver] = useState(false);

  function handleFiles(fileList: FileList | File[] | null) {
    if (!fileList) return;
    const files = Array.from(fileList);
    if (files.length === 0) return;
    setPreviews(files.map((f) => ({ url: URL.createObjectURL(f), name: f.name })));
    onFilesSelected(files);
  }

  return (
    <div
      className={dragOver ? "uploader drag-over" : "uploader"}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        multiple
        hidden
        disabled={disabled}
        onChange={(e) => handleFiles(e.target.files)}
      />
      {previews.length > 0 ? (
        <div className="multi-preview">
          {previews.map((p) => (
            <img key={p.url} src={p.url} alt={p.name} />
          ))}
          <span className="filename">{previews.length} image(s)</span>
        </div>
      ) : (
        <div className="placeholder">
          <strong>{label}</strong>
          <span>Drag & drop 3+ JPG/PNGs, or click to browse</span>
        </div>
      )}
    </div>
  );
}
