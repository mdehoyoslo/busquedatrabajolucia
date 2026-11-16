const VERSION='radar-lucia-2026-v2';const SHELL=['./','./index.html','./style.css','./app.js','./config.js','./manifest.webmanifest','./assets/icon-192.png','./assets/icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(SHELL)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==VERSION).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==location.origin)return; e.respondWith(fetch(e.request).then(res=>{if(res.ok)caches.open(VERSION).then(cache=>cache.put(e.request,res.clone()));return res}).catch(()=>caches.match(e.request)))});
