# Performance Optimization Plan

## Current Performance Analysis

### Asset Loading (base.html)
```html
<!-- Current Setup -->
<script src="https://cdn.tailwindcss.com"></script>                    <!-- Blocking -->
<script defer src="https://cdn.jsdelivr.net/.../alpinejs@3.x.x..."></script>  <!-- Deferred -->
<script src="https://unpkg.com/htmx.org@2.0.4"></script>              <!-- Blocking -->
```

**Issues Identified:**
1. Tailwind CSS loaded via CDN (blocks rendering)
2. HTMX blocks rendering (no defer)
3. Alpine.js properly deferred ✅

---

## Performance Metrics Goals

### Core Web Vitals Targets
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| LCP (Largest Contentful Paint) | < 2.5s | TBD | ⏳ Test needed |
| FID (First Input Delay) | < 100ms | TBD | ⏳ Test needed |
| CLS (Cumulative Layout Shift) | < 0.1 | TBD | ⏳ Test needed |

### Page Load Targets
| Metric | Target | Status |
|--------|--------|--------|
| First Contentful Paint (FCP) | < 1.5s | ⏳ Test needed |
| Time to Interactive (TTI) | < 3.5s | ⏳ Test needed |
| Total Bundle Size | < 500KB | ✅ Likely OK |

---

## Optimization Strategies

### Strategy 1: Script Loading Optimization

#### Current Issue
- Tailwind CSS blocks rendering until downloaded
- HTMX blocks rendering until downloaded

#### Recommended Changes

**1. Defer Tailwind CSS**
```html
<!-- Current (blocking) -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Recommended (non-blocking with fallback) -->
<script defer src="https://cdn.tailwindcss.com"></script>
<!-- Inline critical CSS fallback -->
<style>
  body { font-family: system-ui, -apple-system, sans-serif; }
  /* Critical styles only */
</style>
```

**2. Defer HTMX**
```html
<!-- Current (blocking) -->
<script src="https://unpkg.com/htmx.org@2.0.4"></script>

<!-- Recommended (deferred) -->
<script defer src="https://unpkg.com/htmx.org@2.0.4"></script>
```

**3. Load Custom JS Properly**
```html
<!-- Current (blocking) -->
<script src="{% static 'js/ui-helpers.js' %}"></script>

<!-- Recommended (deferred) -->
<script defer src="{% static 'js/ui-helpers.js' %}"></script>
```

---

### Strategy 2: Critical CSS Inline

Create a minimal critical CSS file with essential styles:
```css
/* Critical CSS (~2KB) */
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: auto; }
body {
  font-family: 'Inter', system-ui, sans-serif;
  background-color: #f9fafb;
  line-height: 1.5;
}
nav { background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
main { max-width: 80rem; margin: 0 auto; padding: 2rem 1rem; }
button, a { cursor: pointer; text-decoration: none; }
input, select, textarea { font: inherit; }
/* Minimize to ~2KB for inline critical CSS */
```

---

### Strategy 3: Image Optimization

#### Current Status
- Product images: Using Django uploads (unknown optimization)
- Logo/icons: Using SVG ✅ (scalable, small)
- Backgrounds: CSS gradients ✅ (no image needed)

#### Recommendations
1. **Lazy Load Images**
   ```html
   <img src="..." loading="lazy" alt="...">
   ```

2. **Responsive Images with srcset**
   ```html
   <img
     src="product-medium.jpg"
     srcset="product-small.jpg 400w, product-medium.jpg 800w, product-large.jpg 1200w"
     alt="Product"
   >
   ```

3. **WebP Format**
   ```html
   <picture>
     <source srcset="image.webp" type="image/webp">
     <img src="image.jpg" alt="...">
   </picture>
   ```

4. **Optimize with ImageOptim/TinyPNG**
   - Reduce JPEG quality to 80-85%
   - Compress PNG with lossless tools
   - Convert to WebP format

---

### Strategy 4: Caching Strategy

#### HTTP Header Caching
```python
# Django settings for caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Set cache headers for static files
# Add to Django middleware or nginx/Apache config
Cache-Control: public, max-age=31536000  # 1 year for versioned assets
Cache-Control: private, max-age=3600     # 1 hour for dynamic content
```

#### Service Worker
```javascript
// Enable offline caching (optional)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
```

---

### Strategy 5: Code Splitting

#### Current Approach
- All JavaScript loaded on every page

#### Optimized Approach
```html
<!-- Load only essential scripts -->
<script defer src="{% static 'js/ui-helpers.js' %}"></script>

<!-- Load page-specific scripts only when needed -->
{% if 'orders' in request.path %}
  <script defer src="{% static 'js/orders.js' %}"></script>
{% endif %}
```

---

### Strategy 6: Minification & Compression

#### Current Status
- Tailwind CSS: Auto-minified by CDN ✅
- Alpine.js: Auto-minified by CDN ✅
- HTMX: Auto-minified by CDN ✅
- Custom JS: Not minified ❌

#### Recommendations
1. **Minify ui-helpers.js**
   ```bash
   npm install -g terser
   terser ui-helpers.js -o ui-helpers.min.js
   ```

2. **Enable Gzip compression** (Django/nginx)
   ```python
   MIDDLEWARE = [
       'django.middleware.gzip.GZipMiddleware',
       # ...
   ]
   ```

3. **Enable Brotli compression** (nginx)
   ```nginx
   gzip on;
   brotli on;
   brotli_types text/plain text/css text/xml text/javascript ...;
   ```

---

### Strategy 7: CDN Usage

#### Current Configuration
- Tailwind: cdn.tailwindcss.com ✅ (Fast, global)
- Alpine.js: cdn.jsdelivr.net ✅ (Fast, reliable)
- HTMX: unpkg.com ⚠️ (Reliable but slower)

#### Optimization
```html
<!-- Upgrade HTMX to faster CDN -->
<!-- Current: unpkg.com -->
<script defer src="https://unpkg.com/htmx.org@2.0.4"></script>

<!-- Better: cdn.jsdelivr.net -->
<script defer src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js"></script>
```

---

### Strategy 8: Font Optimization

#### Current Setup
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
```

**Status:** ✅ Already optimized with:
- Preconnect (reduces DNS lookup)
- Variable fonts (single file for all weights)
- font-display=swap (shows text immediately)

**Further Optimization:**
```html
<!-- Already good, just ensure using local fallback -->
<style>
  @font-face {
    font-family: 'Inter Fallback';
    src: local('Arial'), local('Helvetica'), sans-serif;
  }
  body { font-family: 'Inter', 'Inter Fallback', system-ui, sans-serif; }
</style>
```

---

## Optimization Priority & Timeline

### Phase 1: Quick Wins (1-2 hours)
- [ ] Add `defer` attribute to HTMX and ui-helpers.js scripts
- [ ] Upgrade HTMX CDN to faster provider
- [ ] Minify ui-helpers.js
- [ ] Enable Gzip compression in Django

**Impact:** ~20-30% improvement

### Phase 2: Medium Effort (2-3 hours)
- [ ] Implement lazy loading for images
- [ ] Create critical CSS inline
- [ ] Optimize image assets
- [ ] Add cache headers configuration

**Impact:** ~30-40% improvement

### Phase 3: Advanced (4-6 hours)
- [ ] Implement service worker for offline support
- [ ] Code splitting per page
- [ ] WebP image conversion
- [ ] HTTP/2 server push optimization

**Impact:** ~40-50% improvement

---

## Testing & Monitoring

### Tools to Use
1. **Lighthouse (Chrome DevTools)**
   - Run audit (Ctrl+Shift+I > Lighthouse)
   - Check Performance, Accessibility, SEO

2. **Google PageSpeed Insights**
   - https://pagespeed.web.dev/
   - Real-world performance data

3. **WebPageTest**
   - https://www.webpagetest.org/
   - Detailed waterfall charts

4. **Chrome DevTools Network Tab**
   - Monitor resource loading
   - Check cache behavior
   - Identify bottlenecks

### Performance Baseline
Before making changes, establish baseline:
```
Lighthouse Score: ___ / 100
FCP: ___ ms
LCP: ___ ms
CLS: ___
TTI: ___ ms
Total Size: ___ KB
```

### Post-Optimization Target
```
Lighthouse Score: 90+ / 100
FCP: < 1.5s
LCP: < 2.5s
CLS: < 0.1
TTI: < 3.5s
Total Size: < 500 KB
```

---

## Implementation Checklist

### Immediate (Next Commit)
- [ ] Add `defer` to script tags
- [ ] Upgrade HTMX CDN
- [ ] Test no JavaScript breakage
- [ ] Measure Lighthouse score

### Short Term (Next 2 commits)
- [ ] Minify custom JS
- [ ] Enable Gzip compression
- [ ] Optimize images
- [ ] Test performance improvements

### Medium Term (Future)
- [ ] Implement critical CSS
- [ ] Lazy load images
- [ ] Code splitting
- [ ] Service worker (optional)

---

## Performance Budget

### Recommended Limits
| Resource | Budget | Current | Status |
|----------|--------|---------|--------|
| HTML | 50KB | ~20KB | ✅ OK |
| CSS (Tailwind) | 50KB | ~30KB | ✅ OK |
| JavaScript | 150KB | ~60KB | ✅ OK |
| Images | 250KB | TBD | ⏳ Check |
| Fonts | 50KB | ~20KB | ✅ OK |
| **Total** | **500KB** | **~130KB** | ✅ OK |

---

## Success Criteria

- [ ] Lighthouse score ≥ 90
- [ ] FCP < 1.5 seconds
- [ ] LCP < 2.5 seconds
- [ ] CLS < 0.1
- [ ] Total bundle < 500KB
- [ ] All functionality works after optimizations
- [ ] No visual differences from unoptimized version

---

## Notes

- Performance impacts user experience and SEO
- Optimize for mobile first (40% of web traffic)
- Monitor Core Web Vitals continuously
- Use real user monitoring (RUM) data when available
- Balance performance with functionality and maintainability

