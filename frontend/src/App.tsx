import React from 'react'

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">OVM System</h1>
        <p className="text-gray-600 mb-6">
          Order & Vendor Management System Foundation
        </p>
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-green-600 font-medium">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span>Frontend Ready</span>
          </div>
          <p className="text-sm text-gray-500 italic">
            Phase 0: Base structure initialized.
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
