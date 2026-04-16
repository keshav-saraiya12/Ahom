export default function LoadingSpinner({ className = "" }) {
  return (
    <div className={`flex justify-center items-center py-12 ${className}`}>
      <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
    </div>
  );
}
