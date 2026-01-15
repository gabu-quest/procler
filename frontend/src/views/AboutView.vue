<template>
  <div class="about-view">
    <section class="hero">
      <div class="hero-glow" />
      <div class="hero-content">
        <div class="logo-frame">
          <img src="/procler.png" alt="Procler logo" class="hero-logo" />
        </div>
        <div class="hero-copy">
          <div class="hero-kicker">LLM-first process manager</div>
          <h1>Procler</h1>
          <p class="hero-tagline">
            Orchestrate local and Docker processes with a unified CLI and a real-time dashboard.
            Build repeatable recipes, keep logs close, and ship with confidence.
          </p>
          <div class="hero-actions">
            <n-button type="primary" @click="router.push('/processes')">Open Processes</n-button>
            <n-button secondary @click="router.push('/config')">View Config</n-button>
          </div>
          <div class="hero-tags">
            <n-tag size="small" :bordered="false">local</n-tag>
            <n-tag size="small" :bordered="false">docker</n-tag>
            <n-tag size="small" :bordered="false">recipes</n-tag>
            <n-tag size="small" :bordered="false">vars</n-tag>
          </div>
        </div>
      </div>
    </section>

    <n-grid :cols="3" :x-gap="20" :y-gap="20" responsive="screen" :item-responsive="true">
      <n-gi span="3 m:1">
        <n-card title="What It Does" class="info-card">
          <p>
            Procler keeps process control deterministic: define once, start and stop safely, and
            get status updates and logs in one place. The UI and CLI share the same core logic.
          </p>
        </n-card>
      </n-gi>
      <n-gi span="3 m:1">
        <n-card title="Concepts" class="info-card">
          <ul class="bullet-list">
            <li>Processes live in a single registry.</li>
            <li>Contexts decide where commands run (local or docker).</li>
            <li>Recipes orchestrate multi-step workflows.</li>
            <li>Vars let you template commands with ${VAR}.</li>
          </ul>
        </n-card>
      </n-gi>
      <n-gi span="3 m:1">
        <n-card title="Quick Start" class="info-card">
          <n-code :code="quickStart" class="quick-code" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { NButton, NCard, NGrid, NGi, NTag, NCode } from "naive-ui";

const router = useRouter();

const quickStart = `procler define --name api --command "uvicorn main:app"
procler start api
procler status api
procler logs api --tail 50`;
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
