import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const MermaidComponent = ({ children }: { children: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isZoomed, setIsZoomed] = useState(false);
  const [renderFailed, setRenderFailed] = useState(false);

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
            setRenderFailed(false);
          }
        })
        .catch((error) => {
          console.error('Mermaid render error:', error);
          setRenderFailed(true);
        });
    }
  }, [children]);

  const handleZoomToggle = () => setIsZoomed(!isZoomed);

  if (renderFailed) return null; // ✅ Skip rendering on error

  return (
    <div
      className={`w-full flex justify-center items-center ${isZoomed ? 'fixed inset-0 z-50 bg-black/80 p-4' : ''}`}
      onClick={isZoomed ? handleZoomToggle : undefined}
    >
      <div
        ref={containerRef}
        className={`overflow-x-auto ${isZoomed ? 'bg-white rounded-xl shadow-xl p-4 max-w-6xl w-full max-h-[90vh]' : ''} ${!isZoomed ? 'cursor-zoom-in' : ''}`}
        onClick={(e) => {
          if (!isZoomed) {
            e.stopPropagation();
            handleZoomToggle();
          }
        }}
      />
      {isZoomed && (
        <p className="fixed bottom-4 left-1/2 transform -translate-x-1/2 text-sm text-gray-300">
          Click anywhere to close
        </p>
      )}
    </div>
  );
};

export default MermaidComponent;