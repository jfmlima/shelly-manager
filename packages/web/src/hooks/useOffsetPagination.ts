import { useEffect } from "react";
import type { Dispatch, SetStateAction } from "react";

export const PAGE_SIZE = 50;

/**
 * Step back a page once a page past the first turns out to be empty.
 *
 * Gated on a successful fetch: a transient error also yields zero items and
 * would otherwise rewind pagination the user has not left.
 */
export function useRewindEmptyPage(
  isSuccess: boolean,
  itemCount: number,
  offset: number,
  setOffset: Dispatch<SetStateAction<number>>,
) {
  useEffect(() => {
    if (isSuccess && itemCount === 0 && offset >= PAGE_SIZE) {
      setOffset((current) => Math.max(0, current - PAGE_SIZE));
    }
  }, [isSuccess, itemCount, offset, setOffset]);
}
