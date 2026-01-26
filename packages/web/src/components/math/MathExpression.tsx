"use client";

import { InlineMath, BlockMath } from "react-katex";
import "katex/dist/katex.min.css";

type MathExpressionProps = {
  expression: string;
  display?: boolean; // true for display mode (block), false for inline
  className?: string;
};

/**
 * Renders a LaTeX mathematical expression using KaTeX
 * @param expression - LaTeX code (without $ delimiters)
 * @param display - If true, renders as block math; if false, renders as inline
 * @param className - Additional CSS classes
 */
export function MathExpression({
  expression,
  display = true,
  className = "",
}: MathExpressionProps) {
  try {
    if (display) {
      return (
        <div className={`flex justify-center ${className}`}>
          <BlockMath math={expression} />
        </div>
      );
    } else {
      return <InlineMath math={expression} />;
    }
  } catch (error) {
    // Fallback to raw expression if KaTeX fails
    console.error("KaTeX rendering error:", error);
    return (
      <div className={`text-slate-700 font-mono text-sm ${className}`}>
        {expression}
      </div>
    );
  }
}
