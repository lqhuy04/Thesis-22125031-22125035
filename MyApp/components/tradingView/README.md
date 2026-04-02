# TradingView Component

This component integrates lightweight-charts library for displaying candlestick charts in React Native WebView.

## Local Asset Configuration

The lightweight-charts library is bundled locally instead of loading from CDN to:

-   ✅ Ensure offline functionality
-   ✅ Improve load performance
-   ✅ Avoid external dependencies
-   ✅ Control library version precisely

### File Structure

-   `src/assets/cdnjs/lightweight-charts.standalone.production.js` - Original library file (185KB)
-   `lightweight-charts-inline.ts` - **Generated** TypeScript file with inlined script (187KB)
-   `scripts/generate-inline-script.js` - Script to regenerate the inline file
-   `trading-view-html.ts` - HTML template that uses the inlined script

### Updating the Library

If you need to update the lightweight-charts library:

1. Download the new version to `src/assets/cdnjs/lightweight-charts.standalone.production.js`

2. Regenerate the inline TypeScript file:

    ```bash
    node scripts/generate-inline-script.js
    ```

3. The `lightweight-charts-inline.ts` file will be automatically updated

### Why Inline Instead of Direct Require?

React Native WebView with `html` source property requires:

-   External resources to be loaded from absolute URLs (CDN), OR
-   Scripts to be inlined directly in the HTML

We cannot use relative paths without additional WebView configuration (`baseUrl`, `originWhitelist`). Inlining ensures maximum compatibility and offline support.

### Build Process

The inline script is generated once and committed to the repository. This avoids:

-   Runtime file system access (not available in React Native)
-   Complex metro bundler configuration for .js-as-text
-   Build-time dependencies

The generated file should be committed to git and only regenerated when updating the library version.
