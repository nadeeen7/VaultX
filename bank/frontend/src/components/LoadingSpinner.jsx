export default function LoadingSpinner({ size = "md", text = "Loading..." }) {
  const sizes = {
    sm: "h-5 w-5 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
      <div className={`${sizes[size]} border-gray-200 dark:border-slate-700 border-t-navy-800 dark:border-t-navy-400 rounded-full animate-spin`} />
      {text && <p className="mt-4 text-sm text-gray-500 dark:text-slate-400 font-medium">{text}</p>}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="card p-6 animate-pulse">
      <div className="skeleton h-4 w-32 mb-3" />
      <div className="skeleton h-8 w-48 mb-2" />
      <div className="skeleton h-3 w-24" />
    </div>
  );
}

export function SkeletonLines({ count = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="skeleton h-10 w-10 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="skeleton h-3.5 w-3/4" />
            <div className="skeleton h-3 w-1/2" />
          </div>
          <div className="skeleton h-4 w-16" />
        </div>
      ))}
    </div>
  );
}
