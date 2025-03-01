document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('toggle-mode');
    const body = document.body;
    const icon = toggleButton.querySelector('i');

    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        body.classList.remove('light-mode');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        body.classList.add('light-mode');
        body.classList.remove('dark-mode');
        icon.classList.add('fa-moon');
        icon.classList.remove('fa-sun');
    }

    toggleButton.addEventListener('click', function() {
        body.classList.toggle('dark-mode');
        body.classList.toggle('light-mode');

        if (icon.classList.contains('fa-moon')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            localStorage.setItem('theme', 'dark');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            localStorage.setItem('theme', 'light');
        }
    });

    const urlInput = document.getElementById('url');
    const youtubeOptions = document.getElementById('youtube-options');

    urlInput.addEventListener('input', function() {
        const url = urlInput.value.toLowerCase();
        const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');

        if (isYouTube) {
            youtubeOptions.classList.remove('hidden');
        } else {
            youtubeOptions.classList.add('hidden');
        }
    });

    if (urlInput.value) {
        const url = urlInput.value.toLowerCase();
        const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
        if (isYouTube) {
            youtubeOptions.classList.remove('hidden');
        }
    }

    const downloadForm = document.getElementById('download-form');
    const loadingIndicator = document.getElementById('loading');
    const resultElement = document.querySelector('.result');
    const progressContainer = document.getElementById('progress-container');
    const downloadProgress = document.getElementById('download-progress');
    const progressPercentage = document.getElementById('progress-percentage');

    if (downloadForm) {
        downloadForm.addEventListener('submit', function(e) {
            if (!resultElement || resultElement.classList.contains('hidden')) {
                loadingIndicator.classList.remove('hidden');
                this.style.opacity = '0.5';
                this.style.pointerEvents = 'none';
            }

            const url = urlInput.value.toLowerCase();
            const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');

            if (isYouTube) {
                const selectedQuality = document.querySelector('input[name="quality"]:checked').value;
                let qualityInput = document.querySelector('input[name="selected_quality"]');
                if (!qualityInput) {
                    qualityInput = document.createElement('input');
                    qualityInput.type = 'hidden';
                    qualityInput.name = 'selected_quality';
                    downloadForm.appendChild(qualityInput);
                }
                qualityInput.value = selectedQuality;
            }

            progressContainer.classList.remove('hidden');
            downloadProgress.value = 0;
            progressPercentage.textContent = '0%';

            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                if (progress > 100) progress = 100;
                downloadProgress.value = progress;
                progressPercentage.textContent = `${progress}%`;
                if (progress >= 100) clearInterval(interval);
            }, 500);
        });
    }

    const downloadAnotherBtn = document.getElementById('download-another');
    if (downloadAnotherBtn) {
        downloadAnotherBtn.addEventListener('click', function() {
            window.location.href = '/';
        });
    }

    const platforms = document.querySelectorAll('.platform');
    platforms.forEach(platform => {
        platform.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });

        platform.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    const resultContent = document.querySelector('.result-content');
    if (resultContent) {
        resultContent.addEventListener('click', function() {
            const text = this.textContent;
            const pathMatch = text.match(/to\s+(.+)$/);

            if (pathMatch && pathMatch[1]) {
                const path = pathMatch[1].trim();
                navigator.clipboard.writeText(path).then(() => {
                    const originalBackground = this.style.background;
                    this.style.background = 'rgba(76, 175, 80, 0.2)';

                    setTimeout(() => {
                        this.style.background = originalBackground;
                    }, 1000);

                    let tooltip = document.getElementById('copy-tooltip');
                    if (!tooltip) {
                        tooltip = document.createElement('div');
                        tooltip.id = 'copy-tooltip';
                        tooltip.textContent = 'Path copied!';
                        tooltip.style.position = 'absolute';
                        tooltip.style.background = '#333';
                        tooltip.style.color = '#fff';
                        tooltip.style.padding = '5px 10px';
                        tooltip.style.borderRadius = '4px';
                        tooltip.style.fontSize = '12px';
                        tooltip.style.zIndex = '1000';
                        tooltip.style.opacity = '0';
                        tooltip.style.transition = 'opacity 0.3s';
                        document.body.appendChild(tooltip);
                    }

                    const rect = this.getBoundingClientRect();
                    tooltip.style.top = rect.bottom + 'px';
                    tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
                    tooltip.style.opacity = '1';

                    setTimeout(() => {
                        tooltip.style.opacity = '0';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            }
        });
    }

    if (urlInput) {
        urlInput.addEventListener('input', function() {
            const url = this.value.toLowerCase();
            const platformIcons = document.querySelectorAll('.platform i');

            platformIcons.forEach(icon => {
                icon.parentElement.classList.remove('active-platform');
                icon.parentElement.style.transform = '';
                icon.parentElement.style.boxShadow = '';
            });

            if (url) {
                let detectedIcon = null;

                if (url.includes('youtube') || url.includes('youtu.be')) {
                    detectedIcon = document.querySelector('.platform .fa-youtube');
                } else if (url.includes('instagram') || url.includes('instagr.am')) {
                    detectedIcon = document.querySelector('.platform .fa-instagram');
                } else if (url.includes('facebook') || url.includes('fb.com') || url.includes('fb.watch')) {
                    detectedIcon = document.querySelector('.platform .fa-facebook');
                } else if (url.includes('twitter') || url.includes('x.com') || url.includes('t.co')) {
                    detectedIcon = document.querySelector('.platform .fa-twitter');
                } else if (url.includes('tiktok') || url.includes('tiktok.com') || url.includes('vm.tiktok')) {
                    detectedIcon = document.querySelector('.platform .fa-tiktok');
                } else if (url.includes('reddit') || url.includes('/r/')) {
                    detectedIcon = document.querySelector('.platform .fa-reddit');
                } else if (url.includes('pinterest')) {
                    detectedIcon = document.querySelector('.platform .fa-pinterest');
                }

                if (detectedIcon) {
                    detectedIcon.parentElement.classList.add('active-platform');
                    detectedIcon.parentElement.style.transform = 'scale(1.2) translateY(-5px)';
                    detectedIcon.parentElement.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
                }
            }
        });
    }

    if (urlInput && downloadForm) {
        downloadForm.addEventListener('submit', function(e) {
            const url = urlInput.value.trim();
            const urlPattern = /^(https?:\/\/)?(www\.)?.+\..+/i;

            if (!urlPattern.test(url)) {
                e.preventDefault();
                urlInput.style.border = '2px solid var(--error)';

                let errorMsg = document.getElementById('url-error');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.id = 'url-error';
                    errorMsg.textContent = 'Please enter a valid URL';
                    errorMsg.style.color = 'var(--error)';
                    errorMsg.style.fontSize = '0.8rem';
                    errorMsg.style.marginTop = '-10px';
                    errorMsg.style.marginBottom = '10px';
                    urlInput.parentNode.insertAdjacentElement('afterend', errorMsg);
                }

                setTimeout(() => {
                    urlInput.style.border = '';
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }, 3000);
            }
        });

        urlInput.addEventListener('input', function() {
            this.style.border = '';
            const errorMsg = document.getElementById('url-error');
            if (errorMsg) {
                errorMsg.remove();
            }
        });
    }

    const style = document.createElement('style');
    style.textContent = `
        .active-platform {
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% {
                transform: scale(1.2) translateY(-5px);
            }
            50% {
                transform: scale(1.3) translateY(-7px);
            }
            100% {
                transform: scale(1.2) translateY(-5px);
            }
        }

        .result-content {
            cursor: pointer;
            position: relative;
        }

        .result-content:hover:after {
            content: "Click to copy path";
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: #fff;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
        }
    `;
    document.head.appendChild(style);
});
