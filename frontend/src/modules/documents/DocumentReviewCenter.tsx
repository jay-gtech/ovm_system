import React, { useState } from 'react';
import {
  useDocuments,
  useUploadDocument,
  useApproveDocument,
  useRejectDocument
} from '../../hooks/useDocuments';

export const DocumentReviewCenter: React.FC = () => {
  const { data: documents, isLoading } = useDocuments();
  const uploadMutation = useUploadDocument();
  const approveMutation = useApproveDocument();
  const rejectMutation = useRejectDocument();

  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>('INVOICE');

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (file) {
      uploadMutation.mutate({ file, documentType: docType });
      setFile(null);
    }
  };

  if (isLoading) return <div>Loading documents...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Document Intelligence & Review Center</h1>

      <div className="bg-white p-4 rounded shadow mb-8">
        <h2 className="text-lg font-semibold mb-4">Upload Document</h2>
        <form onSubmit={handleUpload} className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-1">Document Type</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="border p-2 rounded"
            >
              <option value="INVOICE">Invoice</option>
              <option value="PURCHASE_ORDER">Purchase Order</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">File</label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="border p-1 rounded"
            />
          </div>
          <button
            type="submit"
            disabled={!file || uploadMutation.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>
        {uploadMutation.isError && (
          <p className="mt-2 text-sm text-red-600" role="alert">
            Upload failed: {(uploadMutation.error as Error)?.message ?? 'Unknown error. Please try again.'}
          </p>
        )}
        {uploadMutation.isSuccess && (
          <p className="mt-2 text-sm text-green-600">Document uploaded and processing started.</p>
        )}
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-4">Review Queue</h2>
        {documents?.length === 0 ? (
          <p className="text-gray-500">No documents in queue.</p>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b">
                <th className="py-2">Filename</th>
                <th className="py-2">Type</th>
                <th className="py-2">Processing</th>
                <th className="py-2">Validation</th>
                <th className="py-2">Review Status</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents?.map((doc) => (
                <tr key={doc.id} className="border-b">
                  <td className="py-2">{doc.original_filename}</td>
                  <td className="py-2">{doc.document_type}</td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs ${doc.processing_status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                      {doc.processing_status}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs ${doc.validation_status === 'FAILED' ? 'bg-red-100 text-red-800' : doc.validation_status === 'PASSED' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {doc.validation_status}
                    </span>
                  </td>
                  <td className="py-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${doc.human_review_status === 'APPROVED' ? 'text-green-600' : doc.human_review_status === 'REJECTED' ? 'text-red-600' : 'text-yellow-600'}`}>
                      {doc.human_review_status}
                    </span>
                  </td>
                  <td className="py-2 flex gap-2">
                    {doc.processing_status === 'VALIDATED' && doc.human_review_status === 'PENDING' && (
                      <>
                        <button
                          onClick={() => approveMutation.mutate(doc.id)}
                          disabled={approveMutation.isPending}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                        >
                          {approveMutation.isPending ? 'Approving...' : 'Approve'}
                        </button>
                        <button
                          onClick={() => rejectMutation.mutate(doc.id)}
                          disabled={rejectMutation.isPending}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 disabled:opacity-50"
                        >
                          {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
                        </button>
                        {(approveMutation.isError || rejectMutation.isError) && (
                          <span className="text-xs text-red-600" role="alert">
                            Action failed. Please retry.
                          </span>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
