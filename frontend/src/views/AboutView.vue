<template>
  <div class="about-view">
    <section class="hero">
      <div class="hero-glow" />
      <div class="hero-content">
        <div class="logo-frame">
          <img src="/procler.png" alt="Procler logo" class="hero-logo" />
        </div>
        <div class="hero-copy">
          <div class="hero-kicker">{{ $t('about.tagline') }}</div>
          <h1>Procler</h1>
          <p class="hero-tagline">
            {{ $t('about.description') }}
          </p>
          <div class="hero-actions">
            <n-button type="primary" @click="router.push('/processes')">{{ $t('about.openProcesses') }}</n-button>
            <n-button secondary @click="router.push('/config')">{{ $t('about.viewConfig') }}</n-button>
          </div>
          <div class="hero-tags">
            <n-tag size="small" :bordered="false">{{ $t('about.tags.local') }}</n-tag>
            <n-tag size="small" :bordered="false">{{ $t('about.tags.docker') }}</n-tag>
            <n-tag size="small" :bordered="false">{{ $t('about.tags.recipes') }}</n-tag>
            <n-tag size="small" :bordered="false">{{ $t('about.tags.vars') }}</n-tag>
          </div>
        </div>
      </div>
    </section>

    <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
      <n-gi span="3 m:1">
        <n-card :title="$t('about.whatItDoes.title')" class="info-card">
          <p>
            {{ $t('about.whatItDoes.description') }}
          </p>
        </n-card>
      </n-gi>
      <n-gi span="3 m:1">
        <n-card :title="$t('about.concepts.title')" class="info-card">
          <ul class="bullet-list">
            <li>{{ $t('about.concepts.items.processes') }}</li>
            <li>{{ $t('about.concepts.items.contexts') }}</li>
            <li>{{ $t('about.concepts.items.recipes') }}</li>
            <li>{{ $t('about.concepts.items.vars') }}</li>
          </ul>
        </n-card>
      </n-gi>
      <n-gi span="3 m:1">
        <n-card :title="$t('about.quickStart.title')" class="info-card">
          <n-code :code="quickStart" class="quick-code" />
        </n-card>
      </n-gi>

      <!-- Tech Stack Card -->
      <n-gi span="3 m:1">
        <n-card :title="$t('about.techStack.title')" class="info-card tech-stack-card">
          <div class="tech-grid">
            <div class="tech-item">
              <span class="tech-label">{{ $t('about.techStack.backend') }}</span>
              <span class="tech-value">Python 3.12+, FastAPI</span>
            </div>
            <div class="tech-item">
              <span class="tech-label">{{ $t('about.techStack.database') }}</span>
              <span class="tech-value">SQLite + sqler</span>
            </div>
            <div class="tech-item">
              <span class="tech-label">{{ $t('about.techStack.frontend') }}</span>
              <span class="tech-value">Vue 3, Vite, Pinia</span>
            </div>
            <div class="tech-item">
              <span class="tech-label">{{ $t('about.techStack.cli') }}</span>
              <span class="tech-value">Click</span>
            </div>
            <div class="tech-item">
              <span class="tech-label">{{ $t('about.techStack.realtime') }}</span>
              <span class="tech-value">WebSockets</span>
            </div>
          </div>
        </n-card>
      </n-gi>

      <!-- Links Card -->
      <n-gi span="3 m:1">
        <n-card :title="$t('about.links.title')" class="info-card links-card">
          <div class="links-list">
            <a href="https://github.com/gabu-quest/procler" target="_blank" rel="noopener noreferrer" class="link-item">
              <PhGithubLogo class="link-icon" />
              <span>{{ $t('about.links.github') }}</span>
              <PhArrowSquareOut class="link-external" />
            </a>
            <a href="https://pypi.org/project/procler/" target="_blank" rel="noopener noreferrer" class="link-item">
              <PhPackage class="link-icon" />
              <span>{{ $t('about.links.pypi') }}</span>
              <PhArrowSquareOut class="link-external" />
            </a>
          </div>
        </n-card>
      </n-gi>

      <!-- Version & License Card -->
      <n-gi span="3 m:1">
        <n-card class="info-card version-card">
          <div class="version-grid">
            <div class="version-item">
              <span class="version-label">{{ $t('about.version') }}</span>
              <n-tag type="primary" size="small">v{{ version }}</n-tag>
            </div>
            <div class="version-item">
              <span class="version-label">{{ $t('about.license') }}</span>
              <n-tag size="small">MIT</n-tag>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { NButton, NCard, NGrid, NGi, NTag, NCode } from "naive-ui";
import { PhGithubLogo, PhPackage, PhArrowSquareOut } from "@phosphor-icons/vue";

const router = useRouter();

const version = ref("0.1.0");

const quickStart = `procler define --name api --command "uvicorn main:app"
procler start api
procler status api
procler logs api --tail 50`;

onMounted(async () => {
  try {
    const response = await fetch("/api/health");
    if (response.ok) {
      const data = await response.json();
      if (data.version) {
        version.value = data.version;
      }
    }
  } catch {
    // Keep default version
  }
});
</script>

<style scoped>
.about-view {
  max-width: 1200px;
  margin: 0 auto;
}

.hero {
  position: relative;
  padding: 2.5rem 2rem;
  border-radius: 18px;
  background:
    radial-gradient(circle at top left, rgba(0, 229, 255, 0.16), transparent 45%),
    radial-gradient(circle at 20% 120%, rgba(255, 43, 214, 0.12), transparent 55%),
    var(--n-card-color);
  border: 1px solid var(--n-border-color);
  margin-bottom: 2rem;
  overflow: hidden;
}

.hero-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, rgba(0, 229, 255, 0.1), transparent 60%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2rem;
  align-items: center;
}

.logo-frame {
  width: 160px;
  height: 160px;
  border-radius: 24px;
  padding: 10px;
  background: rgba(7, 8, 13, 0.6);
  border: 1px solid rgba(0, 229, 255, 0.25);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-logo {
  width: 100%;
  height: 100%;
  border-radius: 18px;
  object-fit: cover;
}

.hero-copy h1 {
  margin: 0 0 0.5rem;
  font-size: 2.5rem;
}

.hero-kicker {
  font-size: 0.75rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--n-text-color-3);
  margin-bottom: 0.5rem;
}

.hero-tagline {
  color: var(--n-text-color-2);
  font-size: 1rem;
  max-width: 560px;
  margin: 0 0 1.25rem;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.hero-tags {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.info-card p {
  margin: 0;
  color: var(--n-text-color-2);
  line-height: 1.6;
}

.bullet-list {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--n-text-color-2);
  display: grid;
  gap: 0.5rem;
}

.quick-code {
  display: block;
  font-size: 0.85rem;
  line-height: 1.6;
  white-space: pre;
}

/* Tech Stack Card */
.tech-grid {
  display: grid;
  gap: 0.75rem;
}

.tech-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--n-border-color);
}

.tech-item:last-child {
  border-bottom: none;
}

.tech-label {
  font-size: 0.8125rem;
  color: var(--n-text-color-3);
}

.tech-value {
  font-size: 0.875rem;
  color: var(--n-text-color-1);
  font-family: var(--n-font-family-mono);
}

/* Links Card */
.links-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: var(--n-border-radius);
  background: var(--n-code-color);
  color: var(--n-text-color-1);
  text-decoration: none;
  transition: all 0.15s ease;
}

.link-item:hover {
  background: var(--n-primary-color);
  color: var(--n-base-color);
}

.link-icon {
  font-size: 1.25rem;
}

.link-external {
  margin-left: auto;
  font-size: 0.875rem;
  opacity: 0.6;
}

/* Version Card */
.version-grid {
  display: flex;
  justify-content: space-around;
  gap: 2rem;
}

.version-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.version-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--n-text-color-3);
}

@media (max-width: 900px) {
  .hero-content {
    grid-template-columns: 1fr;
  }

  .logo-frame {
    width: 120px;
    height: 120px;
  }
}
</style>
