import React from 'react';

const Logo = ({ className = "h-8", showText = true }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Abstract Signal-Canary Glyph */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-auto"
      >
        <path
          d="M12 4L15 7L12 10L9 7L12 4Z"
          fill="#00FFB2"
        />
        <path
          d="M5 11L12 9L19 11L12 20L5 11Z"
          fill="#00FFB2"
        />
      </svg>

      {showText && (
        <span className="text-xl font-bold font-mono tracking-tight text-foreground">
          Signal<span className="text-[#00FFB2]">Canary</span>
        </span>
      )}
    </div>
  );
};

export default Logo;
