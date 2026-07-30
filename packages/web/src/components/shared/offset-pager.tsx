import type { Dispatch, SetStateAction } from "react";

import { Button } from "@/components/ui/button";
import { PAGE_SIZE } from "@/hooks/useOffsetPagination";

interface OffsetPagerProps {
  offset: number;
  itemCount: number;
  total: number;
  onOffsetChange: Dispatch<SetStateAction<number>>;
}

export function OffsetPager({
  offset,
  itemCount,
  total,
  onOffsetChange,
}: OffsetPagerProps) {
  const rangeStart = total === 0 ? 0 : offset + 1;
  const rangeEnd = offset + itemCount;

  return (
    <div className="flex items-center justify-between pt-4">
      <p className="text-sm text-muted-foreground">
        Showing {rangeStart}–{rangeEnd} of {total}
      </p>
      <div className="space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            onOffsetChange((current) => Math.max(0, current - PAGE_SIZE))
          }
          disabled={offset <= 0}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onOffsetChange((current) => current + PAGE_SIZE)}
          disabled={offset + PAGE_SIZE >= total}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
