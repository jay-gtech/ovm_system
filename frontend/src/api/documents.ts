import apiClient from './client';

export type DocumentType = 'INVOICE' | 'PURCHASE_ORDER' | 'DELIVERY_NOTE' | 'OTHER';
export type DocumentProcessingStatus = 'UPLOADED' | 'OCR_COMPLETE' | 'EXTRACTION_COMPLETE' | 'VALIDATED' | 'FAILED';
export type DocumentValidationStatus = 'PENDING' | 'PASSED' | 'FAILED';
export type DocumentHumanReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface DocumentExtractionResult {
  id: string;
  document_id: string;
  extraction_engine: string;
  extraction_status: 'PENDING' | 'SUCCESS' | 'FAILED';
  raw_ocr_text?: string;
  extracted_fields_json?: Record<string, unknown>;
  confidence_scores_json?: Record<string, unknown>;
  created_at: string;
}

export interface Document {
  id: string;
  document_type: DocumentType;
  original_filename: string;
  mime_type: string;
  file_size: number;
  processing_status: DocumentProcessingStatus;
  validation_status: DocumentValidationStatus;
  human_review_status: DocumentHumanReviewStatus;
  review_required: boolean;
  uploaded_at: string;
  extractions?: DocumentExtractionResult[];
  linked_entity_type?: string;
  linked_entity_id?: string;
}

export const documentApi = {
  upload: async (file: File, documentType: string): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    const { data } = await apiClient.post<Document>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  getAll: async (): Promise<Document[]> => {
    const { data } = await apiClient.get<Document[]>('/documents');
    return data;
  },

  getById: async (id: string): Promise<Document> => {
    const { data } = await apiClient.get<Document>(`/documents/${id}`);
    return data;
  },

  approve: async (id: string): Promise<Document> => {
    const { data } = await apiClient.post<Document>(`/documents/${id}/review/approve`);
    return data;
  },

  reject: async (id: string): Promise<Document> => {
    const { data } = await apiClient.post<Document>(`/documents/${id}/review/reject`);
    return data;
  },
};
