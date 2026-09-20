import { useRef, useState } from "react";
import "./ImageUploader.css";

interface ImageUploaderProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  label?: string;
}

export function ImageUploader({ onFileSelected, disabled, label }: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFile(file: File | undefined) {
    if (!file) return;
    setPreviewUrl(URL.createObjectURL(file));
    setFileName(file.name);
    onFileSelected(file);
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
        handleFile(e.dataTransfer.files[0]);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        hidden
        disabled={disabled}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      {previewUrl ? (
        <div className="preview">
          <img src={previewUrl} alt={fileName ?? "Selected image"} />
          <span className="filename">{fileName}</span>
        </div>
      ) : (
        <div className="placeholder">
          <strong>{label ?? "Upload an image"}</strong>
          <span>Drag & drop a JPG/PNG, or click to browse</span>
        </div>
      )}
    </div>
  );
}
