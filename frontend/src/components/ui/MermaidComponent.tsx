import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const MermaidComponent = ({ children }: { children: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'loose',
      themeVariables: {
        primaryColor: '#f3f4f6',
        primaryTextColor: '#1f2937',
        primaryBorderColor: '#d1d5db',
        lineColor: '#9ca3af',
        fontSize: '16px',
        fontFamily: 'Inter, sans-serif',
        nodeTextColor: '#111827',
        edgeLabelBackground: '#f9fafb',
        clusterBkg: '#fef3c7',
        clusterBorder: '#fde68a',
        defaultLinkColor: '#6b7280',
        noteBkgColor: '#fefce8',
        noteTextColor: '#1f2937',
        actorBorder: '#9ca3af',
        actorBkg: '#f3f4f6',
        signalColor: '#6b7280',
        nodeBorder: '#e5e7eb',
        nodeBkg: '#ffffff',
        nodeRadius: 8
      }
    });

    const uniqueId = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

    if (containerRef.current) {
      mermaid
        .render(uniqueId, children)
        .then(({ svg, bindFunctions }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
            if (bindFunctions) bindFunctions(containerRef.current);
          }
        })
        .catch((error) => {
          console.error('Mermaid render error:', error);
          if (containerRef.current) {
            containerRef.current.innerHTML = '<p style="color: red">⚠️ Failed to render diagram.</p>';
          }
        });
    }
  }, [children]);

  return (
    <div className="w-full flex justify-center items-center">
      <div ref={containerRef} className="overflow-x-auto" />
    </div>
  );
};

export default MermaidComponent;
