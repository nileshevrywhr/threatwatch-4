module.exports = function (api) {
  api.cache(true);

  return {
    presets: [
      ['react-app', { 
        flow: false, 
        typescript: true,
        // Override deprecated plugin proposals with modern transforms
        useBuiltIns: 'entry',
        corejs: 3
      }]
    ],
    plugins: [
      // Use modern transform plugins instead of deprecated proposals
      '@babel/plugin-transform-class-properties',
      '@babel/plugin-transform-private-methods', 
      '@babel/plugin-transform-numeric-separator',
      '@babel/plugin-transform-private-property-in-object',
      '@babel/plugin-transform-nullish-coalescing-operator',
      '@babel/plugin-transform-optional-chaining'
    ],
    env: {
      production: {
        plugins: [
          // Additional production optimizations
          ['transform-remove-console', { exclude: ['error', 'warn'] }]
        ]
      }
    }
  };
};