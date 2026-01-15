import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-gray-200 dark:bg-gray-700", className)}
      {...props}
    />
  )
}

function RecipeCardSkeleton() {
  return (
    <div className="border rounded-lg overflow-hidden">
      <Skeleton className="h-40 sm:h-48 w-full rounded-none" />
      <div className="p-4">
        <Skeleton className="h-6 w-3/4 mb-2" />
        <Skeleton className="h-4 w-1/2 mb-4" />
        <div className="flex gap-2">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
    </div>
  )
}

function RecipeDetailSkeleton() {
  return (
    <div className="max-w-4xl mx-auto">
      <Skeleton className="h-64 w-full mb-6 rounded-lg" />
      <Skeleton className="h-10 w-2/3 mb-4" />
      <div className="flex gap-4 mb-6">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-6 w-24" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div>
          <Skeleton className="h-8 w-32 mb-4" />
          {[1, 2, 3, 4, 5].map(i => (
            <Skeleton key={i} className="h-6 w-full mb-2" />
          ))}
        </div>
        <div className="lg:col-span-2">
          <Skeleton className="h-8 w-32 mb-4" />
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="mb-4">
              <Skeleton className="h-6 w-full mb-2" />
              <Skeleton className="h-6 w-3/4" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export { Skeleton, RecipeCardSkeleton, RecipeDetailSkeleton }
