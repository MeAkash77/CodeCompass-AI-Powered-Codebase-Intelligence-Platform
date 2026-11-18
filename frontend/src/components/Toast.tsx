import { useEffect } from "react"
import "./Toast.css"

interface ToastProps {
  message: string
  type?: "error" | "success" | "warning"
  duration?: number // ms
  onClose: () => void
}

export const Toast = ({ message, type = "error", duration = 3000, onClose }: ToastProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  return (
    <div className={`toast toast-${type}`}>
      {message}
    </div>
  )
}
