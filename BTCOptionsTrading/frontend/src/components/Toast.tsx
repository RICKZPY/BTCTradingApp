import { useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { motion, AnimatePresence } from 'framer-motion'

const Toast = () => {
  const { error, successMessage, setError, setSuccessMessage } = useAppStore()

  useEffect(() => {
    if (error || successMessage) {
      const timer = setTimeout(() => {
        setError(null)
        setSuccessMessage(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, successMessage, setError, setSuccessMessage])

  return (
    <AnimatePresence>
      {(error || successMessage) && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <div
            className={`px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 ${
              error ? 'bg-accent-red' : 'bg-accent-green'
            }`}
          >
            <span className="text-white text-2xl">
              {error ? '❌' : '✅'}
            </span>
            <p className="text-white font-medium">
              {error || successMessage}
            </p>
            <button
              onClick={() => {
                setError(null)
                setSuccessMessage(null)
              }}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default Toast
