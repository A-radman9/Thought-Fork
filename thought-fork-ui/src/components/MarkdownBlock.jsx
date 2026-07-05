/* Copyright 2026 — Apache 2.0 License */

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

/**
 * A reusable component to render Markdown safely and beautifully.
 * Supports tables, GitHub flavored markdown, and raw HTML (like details/summary).
 */
export default function MarkdownBlock({ content }) {
  // Strip out rogue LLM control tags that sometimes leak into the output
  const cleanContent = (content || '')
    .replace(/<\|channel>thought\s*<channel\|>/g, '')
    .replace(/<\|channel>/g, '')
    .replace(/<channel\|>/g, '');

  return (
    <div className="markdown-body">
      <ReactMarkdown 
        remarkPlugins={[remarkGfm]} 
        rehypePlugins={[rehypeRaw]}
      >
        {cleanContent}
      </ReactMarkdown>
    </div>
  );
}
