/**
 * Secure Logger Utility for Production
 * Prevents sensitive data from being logged to console in production
 */

const isDevelopment = process.env.NODE_ENV === 'development';

/**
 * Sanitize objects by removing sensitive fields
 */
const sanitizeObject = (obj) => {
  if (!obj || typeof obj !== 'object') return obj;
  
  const sensitiveFields = [
    'password', 'token', 'access_token', 'refresh_token', 
    'api_key', 'secret', 'auth', 'authorization', 'bearer'
  ];
  
  if (Array.isArray(obj)) {
    return obj.map(sanitizeObject);
  }
  
  const sanitized = {};
  for (const [key, value] of Object.entries(obj)) {
    const keyLower = key.toLowerCase();
    
    // Check if field contains sensitive data
    if (sensitiveFields.some(field => keyLower.includes(field))) {
      sanitized[key] = '***REDACTED***';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeObject(value);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
};

/**
 * Secure console logger
 */
export const secureLog = {
  log: (...args) => {
    if (isDevelopment) {
      const sanitizedArgs = args.map(arg => 
        typeof arg === 'object' ? sanitizeObject(arg) : arg
      );
      console.log(...sanitizedArgs);
    }
  },
  
  warn: (...args) => {
    if (isDevelopment) {
      const sanitizedArgs = args.map(arg => 
        typeof arg === 'object' ? sanitizeObject(arg) : arg
      );
      console.warn(...sanitizedArgs);
    }
  },
  
  error: (...args) => {
    // Always log errors, but sanitize them
    const sanitizedArgs = args.map(arg => 
      typeof arg === 'object' ? sanitizeObject(arg) : arg
    );
    console.error(...sanitizedArgs);
  },
  
  info: (...args) => {
    if (isDevelopment) {
      const sanitizedArgs = args.map(arg => 
        typeof arg === 'object' ? sanitizeObject(arg) : arg
      );
      console.info(...sanitizedArgs);
    }
  }
};

/**
 * Safe user data for logging (removes sensitive fields)
 */
export const sanitizeUserData = (userData) => {
  if (!userData) return null;
  
  const { password, hashed_password, access_token, token, ...safeData } = userData;
  return safeData;
};

export default secureLog;