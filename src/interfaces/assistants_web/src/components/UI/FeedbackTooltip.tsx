import React, { ReactNode, useCallback, useEffect, useRef, useState } from 'react';

import { FeedbackOption } from '@/types/feedbackOption';

export type FeedbackTooltipProps = {
  children: ReactNode;
  options: readonly FeedbackOption[];
  onSend: (startIndex: number, endIndex: number, rating: number) => void;
};

type Selection = {
  range: { start: number; end: number };
  tooltipPosition: { x: number; y: number };
};

export const FeedbackTooltip: React.FC<FeedbackTooltipProps> = ({ children, options, onSend }) => {
  const [selection, setSelection] = useState<Selection | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const getSelectionRange = useCallback(() => {
    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0 || selection.toString().trim().length === 0) {
      return null;
    }

    const range = selection.getRangeAt(0);

    if (!containerRef.current?.contains(range.commonAncestorContainer)) {
      return null;
    }

    return range;
  }, []);

  const getRangeIndexes = useCallback((range: Range) => {
    const globalRange = document.createRange();

    globalRange.setStart(containerRef.current!, 0);
    globalRange.setEnd(range.startContainer, range.startOffset);

    const start = globalRange.toString().length;
    const end = start + range.toString().length - 1;

    return { start, end };
  }, []);

  const clearSelection = useCallback(() => {
    setSelection(null);
  }, []);

  const handleMouseUp = useCallback(() => {
    const range = getSelectionRange();

    if (!range) {
      clearSelection();
      return;
    }

    const { start, end } = getRangeIndexes(range);
    const { right, top } = range.getBoundingClientRect();

    setSelection({
      range: {
        start: start,
        end: end,
      },
      tooltipPosition: {
        x: right,
        y: top,
      },
    });
  }, [getSelectionRange, clearSelection]);

  const handleFeedbackSend = useCallback(
    (rating: number) => {
      if (!selection) {
        return;
      }

      const { start, end } = selection.range;

      onSend(start, end, rating);

      clearSelection();
    },
    [selection, onSend, clearSelection]
  );

  useEffect(() => {
    if (!tooltipRef.current) {
      return;
    }

    document.addEventListener('mousedown', clearSelection);

    return () => document.removeEventListener('mousedown', clearSelection);
  }, [tooltipRef, clearSelection]);

  useEffect(() => {
    if (!selection || !tooltipRef.current) {
      return;
    }

    const { width, height } = tooltipRef.current.getBoundingClientRect();

    setSelection((prev) => ({
      ...prev!,
      tooltipPosition: {
        x: prev!.tooltipPosition.x - width,
        y: prev!.tooltipPosition.y - height - 6,
      },
    }));
  }, [selection?.range, tooltipRef]);

  return (
    <div ref={containerRef} onMouseUp={handleMouseUp}>
      {children}
      {selection && (
        <div
          ref={tooltipRef}
          className="fixed z-50 flex gap-1.5 whitespace-nowrap rounded-xl bg-mushroom-900 p-1.5 shadow-xl dark:bg-volcanic-200"
          style={{
            top: selection.tooltipPosition.y,
            left: selection.tooltipPosition.x,
          }}
        >
          {options.map(({ value, rating }) => (
            <button key={rating} className="text-xl" onClick={() => handleFeedbackSend(rating)}>
              {value}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
