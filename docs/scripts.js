// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.querySelector('.theme-icon');

// Check for saved theme preference or default to light mode
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

themeToggle.addEventListener('click', () => {
    let theme = document.documentElement.getAttribute('data-theme');

    if (theme === 'light') {
        theme = 'dark';
    } else {
        theme = 'light';
    }

    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
});

function updateThemeIcon(theme) {
    if (theme === 'dark') {
        themeIcon.textContent = '☀️';
    } else {
        themeIcon.textContent = '🌙';
    }
}

// Search Functionality
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

// Documentation content index for search
const searchIndex = [
    {
        title: "Getting Started",
        url: "getting-started/index.html",
        excerpt: "Quick start guide to set up your first ambassador in 5 minutes",
        keywords: ["quickstart", "setup", "installation", "first", "begin"]
    },
    {
        title: "Creating Your First Ambassador",
        url: "tutorials/first-ambassador.html",
        excerpt: "Step-by-step tutorial for creating a custom AI ambassador",
        keywords: ["create", "ambassador", "tutorial", "new", "custom"]
    },
    {
        title: "QR Code Setup",
        url: "tutorials/qr-codes.html",
        excerpt: "Configure QR codes for physical-to-digital experiences",
        keywords: ["qr", "code", "physical", "scan", "location"]
    },
    {
        title: "Seeded Demos",
        url: "tutorials/seeded-demos.html",
        excerpt: "Create reproducible demo experiences with synthetic memory",
        keywords: ["demo", "seed", "synthetic", "memory", "reproducible"]
    },
    {
        title: "Custom Agents",
        url: "tutorials/custom-agents.html",
        excerpt: "Build specialized agents with unique capabilities",
        keywords: ["agent", "custom", "build", "capability", "specialized"]
    },
    {
        title: "Power Platform Integration",
        url: "tutorials/power-platform.html",
        excerpt: "Integrate with Microsoft Teams and Microsoft 365 Copilot",
        keywords: ["power", "platform", "teams", "microsoft", "365", "copilot"]
    },
    {
        title: "Multi-Language Support",
        url: "tutorials/multi-language.html",
        excerpt: "Create ambassadors that speak multiple languages",
        keywords: ["language", "multi", "translation", "locale", "international"]
    },
    {
        title: "A/B Testing Ambassadors",
        url: "tutorials/ab-testing.html",
        excerpt: "Test different ambassador configurations and measure performance",
        keywords: ["ab", "test", "testing", "experiment", "measure", "analytics"]
    },
    {
        title: "API Reference",
        url: "api-reference/index.html",
        excerpt: "Complete API endpoint documentation with examples",
        keywords: ["api", "endpoint", "reference", "documentation", "rest"]
    },
    {
        title: "Admin Guide",
        url: "admin-guide/index.html",
        excerpt: "User management, security, monitoring, and system administration",
        keywords: ["admin", "management", "security", "monitoring", "configuration"]
    },
    {
        title: "Deployment Guide",
        url: "deployment/index.html",
        excerpt: "Deploy to Azure with step-by-step instructions",
        keywords: ["deploy", "azure", "production", "infrastructure", "ci", "cd"]
    },
    {
        title: "Troubleshooting",
        url: "troubleshooting/index.html",
        excerpt: "Common issues and solutions for the AI Ambassador Platform",
        keywords: ["troubleshoot", "problem", "error", "issue", "debug", "fix"]
    },
    {
        title: "FAQ",
        url: "faq/index.html",
        excerpt: "Frequently asked questions about the platform",
        keywords: ["faq", "question", "answer", "frequently", "asked"]
    },
    {
        title: "API Explorer",
        url: "api-explorer.html",
        excerpt: "Interactive API testing tool with code generation",
        keywords: ["explorer", "test", "interactive", "playground", "try"]
    }
];

let searchTimeout;

searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);

    const query = e.target.value.trim().toLowerCase();

    if (query.length < 2) {
        searchResults.classList.remove('active');
        searchResults.innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(() => {
        performSearch(query);
    }, 300);
});

function performSearch(query) {
    const results = searchIndex.filter(item => {
        const titleMatch = item.title.toLowerCase().includes(query);
        const excerptMatch = item.excerpt.toLowerCase().includes(query);
        const keywordMatch = item.keywords.some(keyword => keyword.includes(query));

        return titleMatch || excerptMatch || keywordMatch;
    });

    displaySearchResults(results, query);
}

function displaySearchResults(results, query) {
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="search-result-item"><div class="search-result-title">No results found</div></div>';
        searchResults.classList.add('active');
        return;
    }

    const html = results.map(result => {
        const highlightedTitle = highlightText(result.title, query);
        const highlightedExcerpt = highlightText(result.excerpt, query);

        return `
            <a href="${result.url}" class="search-result-item">
                <div class="search-result-title">${highlightedTitle}</div>
                <div class="search-result-excerpt">${highlightedExcerpt}</div>
            </a>
        `;
    }).join('');

    searchResults.innerHTML = html;
    searchResults.classList.add('active');
}

function highlightText(text, query) {
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Close search results when clicking outside
document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.remove('active');
    }
});

// Copy to Clipboard for Code Blocks
function initCodeBlocks() {
    document.querySelectorAll('pre code').forEach((block) => {
        // Wrap code block if not already wrapped
        if (!block.parentElement.classList.contains('code-block-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            block.parentElement.parentNode.insertBefore(wrapper, block.parentElement);
            wrapper.appendChild(block.parentElement);

            // Add copy button
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = 'Copy';
            copyButton.addEventListener('click', () => {
                copyToClipboard(block.textContent, copyButton);
            });

            wrapper.appendChild(copyButton);
        }
    });
}

function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = 'Copy';
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        button.textContent = 'Failed';
    });
}

// Initialize code blocks when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCodeBlocks);
} else {
    initCodeBlocks();
}

// Active Navigation Highlighting
function highlightActiveNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a');

    navLinks.forEach(link => {
        link.classList.remove('active');

        if (link.getAttribute('href') === currentPath ||
            currentPath.includes(link.getAttribute('href'))) {
            link.classList.add('active');
        }
    });
}

// Call on page load
highlightActiveNav();

// Table of Contents Generator
function generateTOC() {
    const headings = document.querySelectorAll('.content h2, .content h3');

    if (headings.length === 0) return;

    const tocContainer = document.querySelector('.toc');
    if (!tocContainer) return;

    const tocList = document.createElement('ul');

    headings.forEach((heading, index) => {
        // Add ID to heading if it doesn't have one
        if (!heading.id) {
            heading.id = `heading-${index}`;
        }

        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `#${heading.id}`;
        a.textContent = heading.textContent;

        if (heading.tagName === 'H3') {
            li.style.paddingLeft = '20px';
        }

        li.appendChild(a);
        tocList.appendChild(li);
    });

    const tocUl = tocContainer.querySelector('ul');
    if (tocUl) {
        tocUl.innerHTML = tocList.innerHTML;
    } else {
        tocContainer.appendChild(tocList);
    }
}

// Generate TOC if container exists
if (document.querySelector('.toc')) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', generateTOC);
    } else {
        generateTOC();
    }
}

// Smooth Scrolling for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));

        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Print Current Version
console.log('AI Ambassador Platform Documentation v1.0.0');
